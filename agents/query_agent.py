"""
Query Agent

Handles queries about ticket status.
Extracts a 6-digit ticket number from the message and looks it up in the DB.
"""

import re
import logging
from db.db_utils import get_ticket

logger = logging.getLogger(__name__)

TICKET_PATTERN = re.compile(r"\b(\d{6})\b")


def _extract_ticket_id(message: str) -> str | None:
    """Return the first 6-digit sequence found in the message, or None."""
    match = TICKET_PATTERN.search(message)
    if match:
        return match.group(1)
    return None


def handle_query(message: str, correlation_id=None) -> dict:
    """
    Handle a query about ticket status.

    Returns dict:
    - "reply": str
    - "ticket_id": str | None
    - "found": bool
    """
    logger.info(
        "QUERY_AGENT_STARTED | correlation_id=%s",
        correlation_id,
    )
    ticket_id = _extract_ticket_id(message)

    if not ticket_id:
        return {
            "reply": (
                "I couldn't find a ticket number in your message. "
                "Please share your 6-digit ticket ID so I can check the status for you."
            ),
            "ticket_id": None,
            "found": False,
        }

    ticket = get_ticket(ticket_id)
    
    logger.info(
        "TICKET_LOOKUP_COMPLETED | correlation_id=%s | ticket_id=%s | found=%s",
        correlation_id,
        ticket_id,
        bool(ticket),
    )

    if ticket is None:
        return {
            "reply": f"I couldn't find any ticket with ID #{ticket_id}. "
                     "Please verify the number and try again.",
            "ticket_id": ticket_id,
            "found": False,
        }

    status = ticket["status"]
    return {
        "reply": f"Your ticket #{ticket_id} is currently marked as: {status}.",
        "ticket_id": ticket_id,
        "found": True,
    }
