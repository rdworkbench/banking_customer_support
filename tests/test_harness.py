# tests/test_harness.py

import sys
import os

# Ensure project root is on Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
"""
System Test Harness for Banking Support AI (LangGraph-based)

Runs a predefined set of customer messages through the system
and prints:
- classification
- agent routing
- ticket creation
- DB validation
- correlation_id (for ops tracing)

This demonstrates end-to-end correctness and LLMOps observability.
"""

from langgraph_impl import run_support_graph
from db.db_utils import get_ticket, init_db
from agents.logger import setup_logging
setup_logging()   # safe for test execution

# -------------------------------------------------
# 1) Test cases (realistic banking scenarios)
# -------------------------------------------------
TEST_CASES = [
    {
        "id": 1,
        "message": "Thank you, your mobile banking app is excellent!",
        "type": "POSITIVE_FEEDBACK",
    },
    {
        "id": 2,
        "message": "Money was debited from my account but ATM did not dispense cash.",
        "type": "NEGATIVE_FEEDBACK",
    },
    {
        "id": 3,
        "message": "What is the status of my ticket 123456?",
        "type": "QUERY",
    },
    {
        "id": 4,
        "message": "Very unhappy with the service. This is unacceptable.",
        "type": "NEGATIVE_FEEDBACK",
    },
    {
        "id": 5,
        "message": "How can I reset my debit card PIN?",
        "type": "QUERY",
    },
    {
        "id": 6,
        "message": "Great support from your call center team.",
        "type": "POSITIVE_FEEDBACK",
    },
    {
        "id": 7,
        "message": "I have an issue with an incorrect charge on my account.",
        "type": "NEGATIVE_FEEDBACK",
    },
    {
        "id": 8,
        "message": "Can you help me check the status of my complaint?",
        "type": "QUERY",
    },
    {
        "id": 9,
        "message": "I am frustrated. My account was debited twice.",
        "type": "NEGATIVE_FEEDBACK",
    },
    {
        "id": 10,
        "message": "Thanks for resolving my issue quickly!",
        "type": "POSITIVE_FEEDBACK",
    },
]

# -------------------------------------------------
# 2) Run harness
# -------------------------------------------------
def run_test_harness():
    print("=" * 80)
    print("BANKING SUPPORT AI – SYSTEM TEST HARNESS")
    print("=" * 80)

    init_db()

    for test in TEST_CASES:
        print("\n" + "-" * 80)
        print(f"TEST CASE {test['id']}")
        print(f"Input Message : {test['message']}")

        result = run_support_graph(
            message=test["message"],
            customer_name="TestUser",
        )

        print(f"Classification : {result.get('classification')}")
        print(f"Handled By     : {result.get('handled_by')}")
        print(f"Reply          : {result.get('reply')}")
        print(f"Correlation ID : {result.get('correlation_id', 'N/A')}")

        ticket_id = result.get("ticket_id")

        if ticket_id:
            print(f"Ticket Created : {ticket_id}")
            ticket = get_ticket(ticket_id)
            if ticket:
                print("DB Verification: SUCCESS")
                print(
                    f"  DB.ticket_id={ticket['ticket_id']} | "
                    f"status={ticket['status']} | "
                    f"correlation_id={ticket['correlation_id']}"
                )
            else:
                print("DB Verification: FAILED (ticket not found)")
        else:
            print("Ticket Created : NO")

    print("\n" + "=" * 80)
    print("TEST HARNESS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_test_harness()
