"""
Feedback Agent

Handles:
- POSITIVE_FEEDBACK: send a warm thank-you message.
- NEGATIVE_FEEDBACK: create a ticket in the DB, return an empathetic reply.
"""

import random
import logging
from typing import Optional

from db.db_utils import create_ticket, get_ticket
from agents.classifier_agent import POSITIVE_FEEDBACK, NEGATIVE_FEEDBACK

logger = logging.getLogger(__name__)

def _generate_unique_ticket_id() -> str:
    """Generate a unique 6-digit ticket ID that is not already in the DB."""
    from db.db_utils import get_ticket  # local import to avoid cycles

    while True:
        ticket_id = f"{random.randint(0, 999999):06d}"
        existing = get_ticket(ticket_id)
        if existing is None:
            return ticket_id


def handle_feedback(message: str, sentiment: str, customer_name: Optional[str] = None, correlation_id=None) -> dict:
    """
    Handle feedback based on sentiment.

    Returns a dict with:
    - "reply": str
    - "ticket_id": str | None
    - "sentiment": str
    """
    logger.info(
        "FEEDBACK_AGENT_STARTED | correlation_id=%s | sentiment=%s",
        correlation_id,
        sentiment
    )
    customer_display = customer_name or "Valued Customer"

    if sentiment == POSITIVE_FEEDBACK:
        reply = (
            f"Thank you for your kind feedback, {customer_display}! "
            "We really appreciate you taking the time to share this with us."
        )
        return {
            "reply": reply,
            "ticket_id": None,
            "sentiment": sentiment,
        }

    if sentiment == NEGATIVE_FEEDBACK:
        ticket_id = _generate_unique_ticket_id()
        # Store the ticket
        create_ticket(
            ticket_id=ticket_id,
            message=message,
            customer_name=customer_name,
            correlation_id=correlation_id,
        )
        reply = (
            f"We're really sorry to hear about your experience, {customer_display}. "
            f"I've created a support ticket for you: #{ticket_id}. "
            "Our team will review this and get back to you as soon as possible."
        )
        return {
            "reply": reply,
            "ticket_id": ticket_id,
            "sentiment": sentiment,
        }

    # Fallback (should not normally happen)
    return {
        "reply": "Thank you for your message.",
        "ticket_id": None,
        "sentiment": sentiment,
    }
