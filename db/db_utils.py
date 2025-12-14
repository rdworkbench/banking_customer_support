import sqlite3
from pathlib import Path
from datetime import datetime

# Path to the SQLite database file (support.db will be created automatically)
DB_PATH = Path(__file__).resolve().parent / "support.db"


def get_connection():
    """Return a SQLite connection to the support.db file."""
    conn = sqlite3.connect(DB_PATH)
    # So we can access columns by name (row["ticket_id"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the support_tickets table if it doesn't exist."""
    schema_file = Path(__file__).resolve().parent / "schema.sql"
    with get_connection() as conn, open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("✅ Database initialized (support_tickets table ready).")


def create_ticket(ticket_id: str, message: str, customer_name: str | None = None, correlation_id: str | None = None) -> None:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO support_tickets
            (ticket_id, customer_name, message, status, created_at, updated_at, correlation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ticket_id, customer_name, message, "Open", now, now, correlation_id),
        )
    print(f"✅ Ticket {ticket_id} created.")


def get_ticket(ticket_id: str) -> dict | None:
    """Fetch a ticket by ticket_id. Return dict or None if not found."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT ticket_id, customer_name, message, status, created_at, updated_at "
            "FROM support_tickets WHERE ticket_id = ?",
            (ticket_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return dict(row)


def update_ticket_status(ticket_id: str, new_status: str) -> None:
    """Update the status of an existing ticket."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE support_tickets
            SET status = ?, updated_at = ?
            WHERE ticket_id = ?
            """,
            (new_status, now, ticket_id),
        )
    print(f"✅ Ticket {ticket_id} status updated to {new_status}.")
