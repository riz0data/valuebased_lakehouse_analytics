# AI Gateway Layer

This folder covers the leg of agentic traffic none of the other layers
touch: the actual outbound call from the agent to a language model
provider. See ADR-015 in `docs/decisions/ADRs.md` for full reasoning.

## How this differs from MCP

This project already has an MCP layer (`.mcp/mcp.json.example`)
governing how the agent reaches tools and the semantic layer. That is
a genuinely different leg of traffic from the one this module covers.
Where AI gateways manage the conversation between agent and model,
MCP gateways manage the conversation between agent and tools. Their
failure modes differ accordingly: this gateway is concerned with
provider outages, rate limits, and budget breaches; MCP is concerned
with tool-level authorization and session integrity. Both layers exist
in this repo now, each scoped to the traffic it actually governs.

## What the gateway does

`model_gateway.py` is a single choke point every model call passes
through, split into a control plane (policy, per-feature daily budget,
and denied-content rules, held as plain configuration) and a data
plane (`route_request()` and `record_response()`, which actually place
and book each call). A request is refused before it goes anywhere if
it would exceed its feature's daily budget or contains disallowed
content - the same enforce-outside-the-model principle already used by
`approval_gate.py` and `sub_agent_delegation.py`. Cost is booked using
the same per-feature rollup pattern as
`observability/finops/agent_cost_tracker.py`.

## Run the demonstration

    python3 observability/ai_gateway/simulate_gateway.py

Covers a normal allowed call, a call refused for tripping the content
policy, and a run of calls refused for exceeding the daily budget.
Real output from that run is saved in `example_gateway_output.txt`.

## Status and limits

This is a reference implementation: a single mocked provider, no real
network calls or API keys, and a simple substring check standing in
for real content-safety classification. It demonstrates the pattern -
split control/data plane, enforced budget, enforced content policy -
rather than being production-ready multi-provider routing.

## Files

- `model_gateway.py` - the gateway itself: routing, budget enforcement,
  content policy.
- `simulate_gateway.py` - runnable demonstration.
- `example_gateway_output.txt` - real output from that run.
