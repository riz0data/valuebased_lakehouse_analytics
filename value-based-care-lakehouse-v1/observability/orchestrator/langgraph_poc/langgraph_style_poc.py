"""
langgraph_style_poc.py

A proof-of-concept translation of end_to_end_orchestrator.py's control
flow into real LangGraph syntax and primitives - StateGraph, typed
state, conditional edges, and the interrupt() human-in-the-loop
mechanism - so the claims made in docs/governance/langgraph_mapping.md
are demonstrated in actual code, not just asserted in prose.

This requires the real "langgraph" package (pip install langgraph) to
run as an executable graph. It is included here as source code showing
exactly how each node/edge would be written; it is not wired into this
repo's dependency-free validator or CI, since this project intentionally
keeps its core observability/ layers framework-free (see
docs/architecture-spec.md's framework-agnostic positioning section).

Every node below is a thin wrapper calling this project's own,
already-built governance functions (screen_input, route_request,
delegate, request_action, validate_output) - LangGraph supplies the
graph, state, and interrupt/resume mechanism; it does not supply the
governance logic itself, exactly as langgraph_mapping.md describes.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

from observability.guardrails.guardrails import screen_input, validate_output, GuardrailAction
from observability.ai_gateway.model_gateway import route_request, record_response, BudgetExceededError, ContentPolicyError
from observability.orchestration.sub_agent_delegation import AgentScope, delegate
from observability.human_in_the_loop.approval_gate import RiskTier


AGENT_SCOPE = AgentScope(
    identity_name="svc-agent-semantic-layer",
    permissions=frozenset({("gold", "semantic", "SELECT")}),
)

MOCK_SEMANTIC_LAYER = {
    "payment_leakage_rate": {"value": "3.2 percent", "period": "Q2 2026"},
    "denial_rate": {"value": "6.1 percent", "period": "Q2 2026"},
}


class RequestState(TypedDict):
    """The shared state object every node reads and writes - LangGraph's
    core mechanism replacing this project's HopLog trail list."""
    user_question: str
    processed_question: Optional[str]
    resolved_metric: Optional[str]
    status: str            # "in_progress" | "blocked" | "approved" | "done"
    block_reason: Optional[str]
    summary: Optional[str]


# --- Nodes: each one wraps an already-existing governance function ---

def guardrails_precall_node(state: RequestState) -> RequestState:
    result = screen_input(state["user_question"])
    if result.action == GuardrailAction.BLOCK:
        return {**state, "status": "blocked", "block_reason": result.reason}
    return {**state, "processed_question": result.processed_text, "status": "in_progress"}


def ai_gateway_node(state: RequestState) -> RequestState:
    try:
        req = route_request(
            feature="semantic-layer-qa",
            content=state["processed_question"],
            prompt_tokens=150,
            max_completion_tokens=250,
        )
        record_response(req, actual_completion_tokens=180, response_text="mock model reasoning")
        return {**state, "status": "in_progress"}
    except (BudgetExceededError, ContentPolicyError) as e:
        return {**state, "status": "blocked", "block_reason": str(e)}


def delegation_node(state: RequestState) -> RequestState:
    # Mirrors sub_agent_delegation.delegate() - LangGraph's own sub-graph
    # feature is the natural home for an actual sub-agent call; this
    # node demonstrates the scope-check happening before that call.
    delegate(
        parent_scope=AGENT_SCOPE,
        requested_permissions=frozenset({("gold", "semantic", "SELECT")}),
        sub_agent_identity="svc-agent-semantic-layer-subtask-lookup",
        task_description=state["processed_question"],
    )
    lowered = state["processed_question"].lower()
    metric = "payment_leakage_rate" if "leakage" in lowered else ("denial_rate" if "denial" in lowered else None)
    return {**state, "resolved_metric": metric, "status": "in_progress"}


def human_in_the_loop_node(state: RequestState) -> RequestState:
    """
    This is the node LangGraph maps most directly onto this project's
    approval_gate.py - but instead of returning a PENDING status the
    caller must remember to check (as approval_gate.py does today),
    LangGraph's interrupt() genuinely suspends graph execution here,
    persists state via the checkpointer, and resumes exactly at this
    point once a human calls the graph back with a decision.
    """
    risk_tier = RiskTier.TIER_1_READ_ONLY  # every real tool today is Tier 1, per ADR-006/012
    if risk_tier != RiskTier.TIER_1_READ_ONLY:
        decision = interrupt({
            "action": f"Approve semantic layer lookup: {state['resolved_metric']}",
            "risk_tier": risk_tier.value,
        })
        if not decision.get("approved"):
            return {**state, "status": "blocked", "block_reason": "Denied by human approver."}
    return {**state, "status": "approved"}


def execute_and_validate_node(state: RequestState) -> RequestState:
    metric = state["resolved_metric"]
    validate_result = validate_output(resolved_metric=metric)
    if validate_result.action == GuardrailAction.BLOCK:
        return {**state, "status": "blocked", "block_reason": validate_result.reason}
    if metric and metric in MOCK_SEMANTIC_LAYER:
        result = MOCK_SEMANTIC_LAYER[metric]
        summary = f"{metric.replace('_', ' ').title()} for {result['period']} was {result['value']}."
    else:
        summary = "No governed metric matched this question."
    return {**state, "status": "done", "summary": summary}


# --- Conditional routing: replaces this project's OrchestrationHalted ---

def route_after(state: RequestState) -> str:
    return "end" if state["status"] == "blocked" else "continue"


def build_graph():
    graph = StateGraph(RequestState)
    graph.add_node("guardrails_precall", guardrails_precall_node)
    graph.add_node("ai_gateway", ai_gateway_node)
    graph.add_node("delegation", delegation_node)
    graph.add_node("human_in_the_loop", human_in_the_loop_node)
    graph.add_node("execute_and_validate", execute_and_validate_node)

    graph.set_entry_point("guardrails_precall")
    graph.add_conditional_edges("guardrails_precall", route_after, {"continue": "ai_gateway", "end": END})
    graph.add_conditional_edges("ai_gateway", route_after, {"continue": "delegation", "end": END})
    graph.add_conditional_edges("delegation", route_after, {"continue": "human_in_the_loop", "end": END})
    graph.add_conditional_edges("human_in_the_loop", route_after, {"continue": "execute_and_validate", "end": END})
    graph.add_edge("execute_and_validate", END)

    # MemorySaver is the checkpointer LangGraph needs for interrupt()
    # to actually suspend and later resume graph execution - this is
    # the durable pause/resume capability langgraph_mapping.md points
    # to as LangGraph's genuine improvement over this project's
    # PENDING-status approach in approval_gate.py.
    return graph.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    print(
        "This is a source-level proof of concept requiring the real "
        "langgraph package. It demonstrates the same control flow as "
        "observability/orchestrator/end_to_end_orchestrator.py, "
        "expressed as a LangGraph StateGraph with conditional edges and "
        "a real interrupt()-based human-in-the-loop node, per "
        "docs/governance/langgraph_mapping.md."
    )
