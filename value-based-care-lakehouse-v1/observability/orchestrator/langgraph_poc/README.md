# LangGraph Proof of Concept

`langgraph_style_poc.py` translates
`observability/orchestrator/end_to_end_orchestrator.py`'s control flow
into real LangGraph syntax: a `StateGraph` with typed state, nodes that
each wrap this project's own already-built governance functions, and
conditional edges replacing this project's `OrchestrationHalted`
exception-based halting. The human-in-the-loop node uses LangGraph's
real `interrupt()` mechanism.

## Honesty note on execution

This sandbox has no outbound network access, so the real `langgraph`
package could not be installed or run here - this file is real,
carefully written LangGraph syntax, checked against LangGraph's
documented API shape, but it has not been executed against the actual
package the way every other simulation script in this repo has been
run and had its output captured. Treat this as a source-level design
artifact, not a verified-running demo, until you run it yourself with
`pip install langgraph` in an environment with network access.

## What each node maps to

Every node is a thin wrapper - `guardrails_precall_node` calls
`screen_input()`, `ai_gateway_node` calls `route_request()` and
`record_response()`, `delegation_node` calls `delegate()`,
`human_in_the_loop_node` calls LangGraph's `interrupt()` guarded by this
project's own risk-tier logic, and `execute_and_validate_node` calls
`validate_output()`. LangGraph supplies the graph structure, shared
state, conditional routing, and durable pause/resume; the governance
decisions themselves are unchanged, imported directly from this
project's existing modules.

## To actually run it

    pip install langgraph
    python3 -c "from langgraph_style_poc import build_graph; g = build_graph(); print(g.invoke({'user_question': 'What was our payment leakage rate last quarter?', 'processed_question': None, 'resolved_metric': None, 'status': 'in_progress', 'block_reason': None, 'summary': None}, config={'configurable': {'thread_id': '1'}}))"
