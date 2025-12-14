"""
Classifier Agent

Classifies incoming customer messages into one of:
- "POSITIVE_FEEDBACK"
- "NEGATIVE_FEEDBACK"
- "QUERY"

Currently uses simple rule-based heuristics.
Later you can plug in an LLM inside `classify_message()`.
"""

import re


POSITIVE_FEEDBACK = "POSITIVE_FEEDBACK"
NEGATIVE_FEEDBACK = "NEGATIVE_FEEDBACK"
QUERY = "QUERY"


def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)


def classify_message(message: str) -> str:
    """
    Classify a customer message into one of the three classes.

    Heuristic baseline:
    - If it clearly looks like a question (question mark, wh-words) → QUERY
    - Else if strong negative words → NEGATIVE_FEEDBACK
    - Else if positive words → POSITIVE_FEEDBACK
    - Else fallback: QUERY
    """
    msg = message.strip()
    msg_lower = msg.lower()

    # 1) Question cues → QUERY
    question_words = ["how", "when", "what", "where", "why", "status", "ticket", "help", "can you", "could you"]
    if "?" in msg or _contains_any(msg, question_words):
        return QUERY

    # 2) Negative sentiment cues
    negative_words = [
        "not happy", "unhappy", "angry", "bad", "worst", "terrible", "horrible",
        "complain", "complaint", "issue", "problem", "frustrated", "disappointed",
        "did not work", "didn't work", "didnt work", "money deducted", "debited but"
    ]
    if _contains_any(msg, negative_words):
        return NEGATIVE_FEEDBACK

    # 3) Positive sentiment cues
    positive_words = [
        "thank you", "thanks", "great", "awesome", "good service", "well done",
        "happy", "satisfied", "love the service"
    ]
    if _contains_any(msg, positive_words):
        return POSITIVE_FEEDBACK

    # 4) Fallback: treat as query
    return QUERY
