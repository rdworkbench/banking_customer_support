# Setup logging
from agents.logger import setup_logging
setup_logging()

import streamlit as st
import pandas as pd
import logging

from db.db_utils import init_db, get_connection
from orchestrator import process_customer_message
from langgraph_impl import run_support_graph


# Initialize DB on app start
init_db()


def load_recent_tickets(limit: int = 20) -> pd.DataFrame:
    """Fetch recent tickets from the DB as a DataFrame."""
    conn = get_connection()
    try:
        query = """
        SELECT ticket_id, customer_name, message, status, created_at, updated_at
        FROM support_tickets
        ORDER BY created_at DESC
        LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
    finally:
        conn.close()
    return df


def main():
    st.set_page_config(page_title="Banking Support AI", page_icon="💬")

    st.title("💬 Banking Customer Support AI (Multi-Agent)")
    st.write(
        "This app classifies customer messages as **positive feedback**, "
        "**negative feedback**, or **query**, and routes them to the "
        "appropriate agent."
    )

    st.sidebar.header("About")
    st.sidebar.markdown(
        """
        **Agents used:**
        - Classifier Agent
        - Feedback Agent (positive / negative)
        - Query Agent (ticket status)
        """
    )

    st.header("1️⃣ Send a Customer Message")

    customer_name = st.text_input("Customer name (optional)", value="")
    message = st.text_area("Customer message", height=150)

    if st.button("Process Message"):
        if not message.strip():
            st.warning("Please enter a message before processing.")
        else:
            # when user clicks "Process Message"
            final_state = run_support_graph(message=message, customer_name=customer_name or None)
            reply = final_state.get("reply", "No response generated. Please retry after sometime")
            
            # Use final_state fields to show UI
            # st.write("Classification:", final_state.get("classification"))
            # st.write("Handled by:", final_state.get("handled_by"))
            # st.info(reply)
            if final_state.get("ticket_id"):
                st.success(f"Ticket ID: #{final_state.get('ticket_id')}")
            # --------------------
            # Simple Orchestrator call

#            result = process_customer_message(
#                message=message,
#                customer_name=customer_name or None,
#            )
#
#            st.subheader("Result")
#            st.write(f"**Classification:** `{result['classification']}`")
#            st.write(f"**Handled by:** `{result['handled_by']}`")
#
#            if result.get("ticket_id"):
#                st.success(f"Ticket ID: #{result['ticket_id']}")

             # -------------------------------

            st.markdown("**Reply to customer:**")
            st.info(reply)

    st.header("2️⃣ Recent Support Tickets")
    with st.expander("Show recent tickets"):
        try:
            df = load_recent_tickets(limit=20)
            if df.empty:
                st.write("No tickets found yet.")
            else:
                st.dataframe(df)
        except Exception as e:
            st.error(f"Error loading tickets: {e}")


if __name__ == "__main__":
    main()
