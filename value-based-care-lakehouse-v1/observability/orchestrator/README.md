# End-to-End Orchestrator

This is the one script that chains every layer built across this
project's agentic AI architecture into a single, real request path,
answering the question the rest of `observability/` was built to
support: what actually happens, step by step, when a person asks this
system a plain-language question. See ADR-016 in
`docs/decisions/ADRs.md` for full reasoning.

## The path a request takes

A question is tagged with the agent's own identity, screened by
pre-call guardrails, routed through the AI gateway's model-leg budget
and content checks, delegated to a sub-agent under constrained
delegation, checked against the MCP-governed semantic-layer access
rule, passed through the human-in-the-loop approval gate, resolved
against the governed semantic layer, validated again by post-call
guardrails, logged for audit and cost, and finally summarized back to
the user. Every one of those steps is real code imported from the
actual module that owns it - `guardrails.py`, `model_gateway.py`,
`sub_agent_delegation.py`, `approval_gate.py` - not reimplemented here.

## What's real versus represented

The enforcement logic at every step is real and actually runs: a
genuine prompt-injection pattern really gets blocked, a genuine
delegation scope check really runs, a genuine approval-tier decision
really gets made. What's represented rather than live is the language
model call itself and the actual warehouse query - there is no live
model and no live Databricks connection in this portfolio project, so
those two points use clearly labeled mock data, consistent with every
other module's reference-implementation framing.

## Run the demonstration

    python3 observability/orchestrator/simulate_end_to_end.py

Covers three scenarios: a normal question that flows successfully
through all nine enforcement points to a correct governed-metric
answer, a question containing a prompt-injection attempt halted at
guardrails before it ever reaches the model, and a hypothetical
higher-risk action halted at the human-in-the-loop gate pending
approval. Real output from that run is saved in
`example_end_to_end_output.txt`.

## Why this is framework-free

This orchestrator is plain Python with no agent framework dependency,
deliberately - see the framework-agnostic positioning section in
`docs/architecture-spec.md`. The two companion documents
`docs/governance/agent_bricks_mapping.md` and
`docs/governance/langgraph_mapping.md` show how this exact same
control flow would be re-expressed using Databricks Agent Bricks or
LangGraph specifically, so the architecture is provably portable rather
than tied to any one execution substrate.

## Files

- `end_to_end_orchestrator.py` - the orchestrator itself.
- `simulate_end_to_end.py` - runnable demonstration, three scenarios.
- `example_end_to_end_output.txt` - real output from that run.
