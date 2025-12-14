"""
Classifier Agent (LLM-backed with heuristic fallback)

This module exposes classify_message(message, use_llm=True) -> str
Possible return values:
- POSITIVE_FEEDBACK
- NEGATIVE_FEEDBACK
- QUERY

Behavior:
- If use_llm=True, attempts to call the OpenAI Chat API to classify the message.
- If the API call fails, times out, or returns an unexpected answer, falls back
  to the original rule-based heuristic classifier.
- The model name can be set via environment variable OPENAI_MODEL (default 'gpt-4').
- Requires OPENAI_API_KEY in environment for LLM usage.
"""

from __future__ import annotations
import os
import re
import logging
import time
from typing import Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Local heuristic fallback (keeps previous behavior)
def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)

def heuristic_classify(message: str) -> str:
    msg = message.strip()
    msg_lower = msg.lower()

    # 1) Question cues → QUERY
    question_words = ["how", "when", "what", "where", "why", "status", "ticket", "help", "can you", "could you"]
    if "?" in msg or _contains_any(msg, question_words):
        return "QUERY"

    # 2) Negative sentiment cues
    negative_words = [
        "not happy", "unhappy", "angry", "bad", "worst", "terrible", "horrible",
        "complain", "complaint", "issue", "problem", "frustrated", "disappointed",
        "did not work", "didn't work", "didnt work", "money deducted", "debited but"
    ]
    if _contains_any(msg, negative_words):
        return "NEGATIVE_FEEDBACK"

    # 3) Positive sentiment cues
    positive_words = [
        "thank you", "thanks", "great", "awesome", "good service", "well done",
        "happy", "satisfied", "love the service"
    ]
    if _contains_any(msg, positive_words):
        return "POSITIVE_FEEDBACK"

    # 4) Fallback: treat as query
    return "QUERY"


# ---------- LLM integration ----------
# Attempt to import openai only when required to avoid import errors if not installed.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")  # configurable; change if needed
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "10"))  # seconds



def _safe_import_openai():
    try:
        import openai  # type: ignore
        return openai
    except Exception as e:
        logger.warning("openai package not available in the environment (%s).", e)
        return None


def _call_openai_chat(message: str, model: str = OPENAI_MODEL, timeout: float = OPENAI_TIMEOUT) -> Optional[str]:
    """
    Calls OpenAI ChatCompletion with a constrained prompt asking for a single label.
    Returns the raw text response or None on failure.
    """
    openai = _safe_import_openai()
    if openai is None:
        return None

    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not found in environment; skipping LLM call.")
        return None

    # Configure api key from env (openai picks it up automatically, but set explicitly for clarity)
    openai.api_key = OPENAI_API_KEY

    system_prompt = (
        "You are a strict classifier. Classify the user's message into EXACTLY ONE of the following labels:\n"
        "- POSITIVE_FEEDBACK\n"
        "- NEGATIVE_FEEDBACK\n"
        "- QUERY\n\n"
        "Return only the label, and nothing else (no punctuation, no explanation). "
        "If the message contains both a complaint and a question, prefer QUERY only if the user explicitly asks about ticket status; "
        "otherwise prefer NEGATIVE_FEEDBACK for complaints. Be concise and deterministic."
    )

    user_prompt = (
        f"Message: \"{message}\"\n\n"
        "Which single label from the list applies? Reply with only the label."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # We'll do a small retry loop for transient errors
    retries = 2
    for attempt in range(1, retries + 1):
        try:
            # Use ChatCompletion API
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=8,
                n=1,
                request_timeout=timeout,
            )
            # Extract text
            content = ""
            if resp and "choices" in resp and len(resp["choices"]) > 0:
                content = resp["choices"][0]["message"]["content"].strip()
            if content:
                return content
            else:
                logger.warning("Empty response from OpenAI on attempt %s", attempt)
        except Exception as e:
            logger.warning("OpenAI call failed on attempt %s: %s", attempt, e)
            # small backoff
            time.sleep(0.5 * attempt)

    return None


def _normalize_label(text: str) -> Optional[str]:
    """
    Normalize the model output to one of the three canonical labels.
    If it cannot be mapped, return None.
    """
    if not text:
        return None

    t = text.strip().upper()
    # direct matches
    for lbl in ("POSITIVE_FEEDBACK", "NEGATIVE_FEEDBACK", "QUERY"):
        if t == lbl:
            return lbl

    # Accept some common shorthand or accidental punctuation
    t_clean = re.sub(r"[^A-Z_]", "", t)  # remove punctuation / numbers, keep letters & underscore
    if t_clean in ("POSITIVEFEEDBACK", "POSITIVE_FEEDBACK", "POSITIVE", "THANKS"):
        return "POSITIVE_FEEDBACK"
    if t_clean in ("NEGATIVEFEEDBACK", "NEGATIVE_FEEDBACK", "NEGATIVE", "COMPLAINT", "COMPLAIN"):
        return "NEGATIVE_FEEDBACK"
    if t_clean in ("QUERY", "QUESTION", "STATUS", "TICKET"):
        return "QUERY"

    # try to detect keywords if LLM gave a short phrase
    t_lower = t.lower()
    if any(k in t_lower for k in ["thank", "thanks", "great", "good", "happy", "satisfied"]):
        return "POSITIVE_FEEDBACK"
    if any(k in t_lower for k in ["not", "unhappy", "angry", "complain", "debit", "issue", "problem", "frustrat"]):
        return "NEGATIVE_FEEDBACK"
    if any(k in t_lower for k in ["?", "how", "what", "when", "status", "ticket", "help"]):
        return "QUERY"

    return None


def classify_message(message: str, use_llm: bool = True) -> str:
    """
    Public function to classify a message.

    Parameters:
    - message: the customer message
    - use_llm: if True, try LLM first; if False, use heuristic only.

    Returns one of:
    - 'POSITIVE_FEEDBACK', 'NEGATIVE_FEEDBACK', 'QUERY'
    """
    message = (message or "").strip()
    if not message:
        logger.info("Empty message provided to classify_message; returning QUERY by default.")
        return "QUERY"

    # If LLM usage is disabled explicitly, use heuristic directly
    if not use_llm:
        return heuristic_classify(message)

    # Try LLM
    raw = _call_openai_chat(message)
    if raw:
        label = _normalize_label(raw)
        if label:
            logger.info("LLM classification succeeded: %s -> %s", message[:60], label)
            return label
        else:
            logger.warning("LLM returned unexpected label '%s'; falling back to heuristic.", raw)

    # Fallback to heuristic
    fallback = heuristic_classify(message)
    logger.info("Heuristic fallback classification: %s -> %s", message[:60], fallback)
    return fallback


# Keep the old label constants for compatibility with existing code
POSITIVE_FEEDBACK = "POSITIVE_FEEDBACK"
NEGATIVE_FEEDBACK = "NEGATIVE_FEEDBACK"
QUERY = "QUERY"


# Quick CLI-like test when run as script
if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "I want to know the status of my ticket 123456"
    print("Input:", msg)
    print("Classification (LLM preferred):", classify_message(msg, use_llm=True))
    print("Classification (heuristic only):", classify_message(msg, use_llm=False))
