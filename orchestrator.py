"""
Orchestrator

Wires together:
- Classifier Agent
- Feedback Agent
- Query Agent
"""

from typing import Optional

from agents.classifier_agent import (
    classify_message,
    POSITIVE_FEEDBACK,
    NEGATIVE_FEEDBACK,
    QUERY,
)
from agents.feedback_agent import handle_feedback
from agents.query_agent import handle_query


def process_customer_message(message: str, customer_name: Optional[str] = None) -> dict:
    """
    Main entry point for processing a customer message.

    Returns a dict with:
    - "original_message": str
    - "classification": str  (one of the 3 labels)
    - "handled_by": str      ("FeedbackAgent" or "QueryAgent")
    - "reply": str
    - "ticket_id": str | None
    - Additional info per agent if needed
    """
    classification = classify_message(message)

    if classification in {POSITIVE_FEEDBACK, NEGATIVE_FEEDBACK}:
        result = handle_feedback(message=message, sentiment=classification, customer_name=customer_name)
        return {
            "original_message": message,
            "classification": classification,
            "handled_by": "FeedbackAgent",
            "reply": result["reply"],
            "ticket_id": result["ticket_id"],
        }

    if classification == QUERY:
        result = handle_query(message=message)
        return {
            "original_message": message,
            "classification": classification,
            "handled_by": "QueryAgent",
            "reply": result["reply"],
            "ticket_id": result["ticket_id"],
        }

    # Fallback (shouldn't happen)
    return {
        "original_message": message,
        "classification": classification,
        "handled_by": "Unknown",
        "reply": "I'm not sure how to handle this message.",
        "ticket_id": None,
    }


if __name__ == "__main__":
    # Simple manual test
    samples = [
        "Thank you, the app is really good!",
        "I am very disappointed, my money was debited but I didn't receive cash.",
        "What is the status of my ticket 123456?",
    ]
    for msg in samples:
        print("\nMessage:", msg)
        out = process_customer_message(msg, customer_name="Test User")
        print("Result:", out)
