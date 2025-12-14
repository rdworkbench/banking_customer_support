# langgraph_impl.py
from typing_extensions import TypedDict
from datetime import datetime
import logging

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import uuid

from agents.classifier_agent import (
    classify_message,
    POSITIVE_FEEDBACK,
    NEGATIVE_FEEDBACK,
    QUERY,
)
from agents.feedback_agent import handle_feedback
from agents.query_agent import handle_query


logger = logging.getLogger(__name__)

# -------------------------------------------------
# 1) Define Graph State
# -------------------------------------------------
class SupportState(TypedDict, total=False):
    message: str
    customer_name: str | None
    correlation_id: str 
    classification: str
    handled_by: str
    ticket_id: str | None
    reply: str
    processed_at: str


# -------------------------------------------------
# 2) Define Nodes
# -------------------------------------------------
def node_classifier(state: SupportState) -> dict:
    logger.info(
        "CLASSIFICATION_STARTED | correlation_id=%s | message=%s",
        state["correlation_id"],
        state["message"][:80],
    )
    cls = classify_message(state["message"])
    logger.info(
        "CLASSIFICATION_COMPLETED | correlation_id=%s | classification=%s",
        state["correlation_id"],
        cls,
    )
    return {"classification": cls}


def node_feedback(state: SupportState) -> dict:
    logger.info(
        "Running Feedback Agent | correlation_id=%s",
        state["correlation_id"]
    )
    result = handle_feedback(
        message=state["message"],
        sentiment=state["classification"],
        customer_name=state.get("customer_name"),
        correlation_id=state["correlation_id"],
    )
    return {
        "reply": result["reply"],
        "ticket_id": result["ticket_id"],
        "handled_by": "FeedbackAgent",
        "processed_at": datetime.utcnow().isoformat(),
    }


def node_query(state: SupportState) -> dict:
    logger.info("Running Query Agent")
    result = handle_query(
      message=state["message"],
      correlation_id=state["correlation_id"],
    )
    return {
        "reply": result["reply"],
        "ticket_id": result["ticket_id"],
        "handled_by": "QueryAgent",
        "processed_at": datetime.utcnow().isoformat(),
    }


# -------------------------------------------------
# 3) Routing Logic
# -------------------------------------------------
def route_after_classification(state: SupportState) -> str:
    cls = state["classification"]
    logger.info(
        "ROUTING_DECISION | correlation_id=%s | next_agent=%s",
        state["correlation_id"],
        "FeedbackAgent" if cls != QUERY else "QueryAgent",
    )

    if cls in (POSITIVE_FEEDBACK, NEGATIVE_FEEDBACK):
        return "feedback"
    return "query"


# -------------------------------------------------
# 4) Build Graph WITH Checkpointing
# -------------------------------------------------
def build_support_graph():
    graph = StateGraph(SupportState)

    graph.add_node("classifier", node_classifier)
    graph.add_node("feedback", node_feedback)
    graph.add_node("query", node_query)

    graph.add_edge(START, "classifier")

    graph.add_conditional_edges(
        "classifier",
        route_after_classification,
        {
            "feedback": "feedback",
            "query": "query",
        },
    )

    graph.add_edge("feedback", END)
    graph.add_edge("query", END)

    # CHECKPOINTING ADDITION
    checkpointer = MemorySaver()

    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph, checkpointer


# Build once
GRAPH, CHECKPOINTER = build_support_graph()


# -------------------------------------------------
# 5) Public Runner
# -------------------------------------------------
def run_support_graph(message: str, customer_name: str | None = None) -> dict:
    correlation_id = f"cs-{uuid.uuid4()}"
    """
    Runs the LangGraph with checkpointing enabled.
    """
    logger.info(
        "REQUEST_RECEIVED | correlation_id=%s | customer=%s",
        correlation_id,
        customer_name or "NA",
    )
    initial_state: SupportState = {
        "message": message,
        "customer_name": customer_name,
        "correlation_id": correlation_id,
    }

    # Each run MUST have a thread_id for checkpointing
    config = {
        "configurable": {
            "thread_id": correlation_id
        }
    }

    final_state = GRAPH.invoke(initial_state, config=config)
    logger.info(
      "REQUEST_COMPLETED | correlation_id=%s | handled_by=%s",
      correlation_id,
      final_state.get("handled_by"),
    )
    return dict(final_state)
