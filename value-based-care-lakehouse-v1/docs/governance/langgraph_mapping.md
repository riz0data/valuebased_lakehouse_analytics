# Mapping This Architecture onto LangGraph

This is the companion to `agent_bricks_mapping.md` and the
framework-agnostic positioning section in `docs/architecture-spec.md`.
Where the Agent Bricks mapping is about a managed platform, this
mapping is about a lower-level orchestration library, and the overlap
with this project's design is more structural: LangGraph's own
documentation states it is focused on the underlying capabilities
important for agent orchestration - durable execution, streaming,
human-in-the-loop, and more - which is close to what this repo's
`observability/orchestrator/end_to_end_orchestrator.py` demonstrates by
hand.

## The core structural match

LangGraph models an agent as a graph: nodes are functions that read and
write to a shared state object, and edges connect nodes either
unconditionally or conditionally - go to one node if a condition holds,
another node otherwise. This project's `end_to_end_orchestrator.py`
already has this shape even without LangGraph: it is a fixed sequence
of steps (identity, guardrails, gateway, delegation, MCP access, HITL,
execution, guardrails, logging, summary) with explicit halt conditions
at several points. Translating it onto LangGraph means turning each
numbered step into a graph node and each `OrchestrationHalted` raise
into a conditional edge that routes to an end state instead of the next
node - the control flow does not change, only its representation.

## Layer-by-layer mapping

**Guardrails (pre-call and post-call).** These become two ordinary
graph nodes, each reading the shared state (the user's question, or the
resolved metric) and either updating state to continue or routing to a
"blocked" terminal node via a conditional edge - no different in
substance from the direct function calls this repo uses today.

**AI Gateway.** The model-leg budget and content check becomes a node
that runs immediately before the node that actually invokes the LLM.
LangGraph does not include a gateway itself - a real deployment would
still need this repo's `model_gateway.py` logic, or a dedicated AI
gateway product, invoked from within that node.

**Human-in-the-loop.** This is LangGraph's most direct, well-documented
overlap with this project. LangGraph treats human-in-the-loop as a core
runtime capability, not an add-on: its interrupt mechanism pauses
execution, saves state, and waits for human input without blocking
threads, and when the human responds, execution resumes from the exact
point it paused. That is a more capable version of the same principle
`approval_gate.py` implements by hand - this repo's gate returns a
PENDING status and relies on the calling code to halt; LangGraph's
`interrupt` actually suspends and durably persists the graph's
execution state via its checkpointer, so a real deployment resumes
mid-graph rather than needing to be re-invoked from the start. The
four-tier risk model and SLA structure this repo defines would still be
this project's own logic, deciding which tier routes to an interrupt
versus which auto-proceeds - LangGraph provides the suspend/resume
mechanism, not the risk policy itself.

**Orchestration / constrained delegation.** LangGraph's graphs
naturally support sub-graphs, where one node's execution is itself
another graph - a structural fit for delegating a sub-task to a
sub-agent. But LangGraph does not enforce anything about what
permissions a sub-graph inherits from its parent; the
`ScopeEscalationError` subset check in `sub_agent_delegation.py` is
this project's own governance logic and would need to run as an
explicit check inside whatever node invokes the sub-graph, exactly as
it does today.

**Identity and the AI Gateway's cost/budget tracking** are similarly
not native LangGraph concepts - LangGraph manages control flow and
state, not identity or billing. Both would remain this project's own
logic, called from within LangGraph nodes rather than replaced by
LangGraph itself.

## Honest summary

LangGraph is the closer structural match of the two frameworks
discussed in this repo's mapping docs, specifically because
human-in-the-loop and durable, resumable execution are first-class
LangGraph primitives rather than bolted on. Identity, the AI gateway's
budget/content policy, and constrained delegation's scope enforcement
remain this project's own governance logic regardless - LangGraph
gives them a more capable execution substrate to run inside (real
pause/resume, real state persistence via a checkpointer) but does not
supply the policy decisions themselves.
