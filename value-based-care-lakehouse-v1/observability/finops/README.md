# FinOps Layer

This folder extends the observability layer (see `../README.md` and
ADR-008) with cost attribution, split into the two halves that actually
have different cost mechanisms: lakehouse compute cost, and agent/AI
cost. See ADR-011 in `docs/decisions/ADRs.md` for the full design
reasoning.

## Lakehouse compute cost

`lakehouse_cost_attribution.sql` sources real dollar cost from
Databricks' own system tables - `system.billing.usage` joined against
`system.billing.list_prices` - grouped by the custom tags (project,
team, environment) attached to each cluster, job, or SQL warehouse.
This is not an estimate: DBU consumption and per-DBU pricing both come
directly from Databricks' own billing data.

This depends entirely on tagging being set correctly at cluster and job
creation time. The query includes a separate untagged-spend check,
since untagged compute is the first thing a real FinOps review would
chase down - it can't be charged back to anyone until it's tagged.

Not runnable from this repo (no live workspace is attached to this
portfolio project). See `example_lakehouse_cost_output.txt` for an
illustrative result set showing the shape of the output.

## Agent/AI cost

`agent_cost_tracker.py` extends the existing agent audit log
(`observability/mcp_audit_logger.py`, ADR-008) with a sibling cost
event: token counts read from the model provider's response at call
time, converted to dollars via a maintained per-model rate lookup
table, tagged with the feature that triggered the call. This rides on
the audit log this project already has rather than standing up a
second, disconnected logging pipeline.

Run the local, dependency-free simulation directly:

    python3 observability/finops/simulate_agent_cost.py

It prints a simulated day of agent calls, their token counts and
computed dollar cost, and the resulting cost-by-feature rollup. Real
output from that run is saved in `example_agent_cost_output.txt`.

**Honest limitation:** token cost is a necessary but partial view of
real agentic cost. A single user question can trigger multiple tool
calls and retries, so the real cost driver in production is calls per
task, not tokens per call alone. This module tracks token cost
accurately; it does not model retry or orchestration overhead, which a
real deployment should track as its own metric alongside this one.

## Files

- `lakehouse_cost_attribution.sql` - Databricks system-table query for
  compute cost, grouped by tag.
- `example_lakehouse_cost_output.txt` - illustrative result set.
- `agent_cost_tracker.py` - cost event schema, batch logger, and
  daily-cost-by-feature rollup, meant to run as a sibling Databricks Job
  to `mcp_audit_logger.py`.
- `simulate_agent_cost.py` - runnable, dependency-free local simulation
  of the agent cost logic.
- `example_agent_cost_output.txt` - real output from running the
  simulation above.
