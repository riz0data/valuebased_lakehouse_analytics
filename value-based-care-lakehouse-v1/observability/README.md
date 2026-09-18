# Observability

This folder demonstrates continuous audit logging and alerting for AI
agent access to this project's governed metrics - see ADR-008 in
`docs/decisions/ADRs.md` for the full design reasoning.

**Important context: no agent is actually deployed against this
project.** Everything here is a reference implementation and a runnable
simulation, not a live monitoring pipeline or captured production
traffic. The goal is to make the mechanism concrete, correct, and
verifiable, not to claim a running system exists.

## Files

- `mcp_audit_logger.py` - the real Databricks Job implementation.
  Two functions, meant to run as scheduled tasks on a 1-minute cadence:
  `log_agent_activity_batch()` appends buffered tool-call events to a
  Delta table (`gold.observability.agent_query_log`); 
  `check_for_agent_anomalies()` reads that table's most recent window
  and evaluates three rules - error rate, repeated identical calls, and
  latency spikes - writing to `gold.observability.agent_alerts` and
  firing a notification whenever one trips. This file requires a live
  SparkSession and Databricks workspace to actually run, so it prints a
  short explanation rather than executing if run standalone.
- `simulate_agent_session.py` - a dependency-free reimplementation of
  the exact same event schema and the exact same three alert rules,
  over a plain Python list instead of a Delta table. Run it directly
  (`python3 simulate_agent_session.py`) to see the logic actually work,
  no Spark or Databricks required.
- `example_simulation_output.txt` - real, captured output from running
  `simulate_agent_session.py`: a healthy 3-call session that correctly
  triggers no alerts, followed by a simulated stuck-loop session (an
  agent retrying a nonexistent metric 8 times) that correctly trips all
  three rules at once.

## Why a 1-minute batch job, not true streaming

`log_agent_activity_batch()` is a scheduled micro-batch write
(`.write.format("delta").mode("append")` on a 1-minute trigger), not a
continuously-running Structured Streaming query. A 1-minute freshness
requirement is exactly the kind of lenient-latency case Databricks'
own documentation recommends handling with a one-time-trigger batch job
rather than a persistent stream - simpler to operate, and more than
fast enough to catch a misbehaving agent before it causes real damage.

## The three alert rules

- **High error rate** - more than 20 percent of calls in the last
  minute failed. Catches an agent hitting a systemic problem (a broken
  metric reference, a permissions issue) rather than one-off, expected
  failures like a legitimate "no matching metric" response.
- **Repeated identical calls** - the same tool called with the exact
  same arguments 5 or more times in the window. Catches a stuck retry
  loop while it's happening, the scenario ADR-008 specifically calls
  out: a passive log would only reveal this after the fact, once
  someone happened to read it.
- **Latency spike** - p99 latency over 5 seconds in the window. Catches
  a tool or dependency degrading before it turns into a full outage.

All three are simple, fixed thresholds, not a learned anomaly model, on
purpose - anyone reading this repo can see exactly why an alert fired.
They would need real tuning against actual traffic once an agent is
truly deployed; see ADR-008's trade-offs section.

## How alerting actually reaches a person

`send_alert()` in `mcp_audit_logger.py` is a stand-in - in a real
deployment, the simplest real path needs no custom notification code at
all: point a Databricks SQL Alert at
`gold.observability.agent_alerts` on the same 1-minute schedule, and
Databricks handles the email or Slack webhook itself the moment a new
row appears.

## What this still doesn't cover

This covers reliability signals: errors, stuck loops, and latency. It
does not cover answer-quality signals - whether the agent picked the
*right* metric for a given question, whether a number it returned was
actually correct - which would need a separate evaluation harness, nor
does it cover drift detection, which remains a natural next layer, not
implemented here. Cost and token telemetry, once a natural next layer
too, is now covered - see `finops/`.


## Evaluation: is the agent giving *correct* answers?

Everything above covers reliability - errors, stuck loops, latency. It
says nothing about whether an agent's successful, fast, confidently-
returned answer was actually the *right* metric for the question asked.
That's a separate concern, covered in `evaluation/` - a three-layer
harness (deterministic checks, golden-dataset regression testing, and
rubric-based scoring) evaluated against real synonyms already defined
in `_metrics.yml`. See `evaluation/README.md` and ADR-009.


## Guardrails: stopping bad calls before they happen

Everything above is reactive - it detects problems after a call
completes. `guardrails/` is the one piece that acts before a bad
question reaches the model and before a bad answer reaches the user:
pre-call screening for prompt injection and sensitive data, and
post-call validation that a claimed metric actually exists. See
`guardrails/README.md` and ADR-010.


## FinOps: what does the agent, and the lakehouse under it, actually cost?

Everything above covers behavior and correctness. `finops/` covers
money: real Databricks system-table-sourced compute cost attribution
for the lakehouse side, and call-level token cost attribution for the
agent side, both extending the same audit log this project already
has rather than standing up a separate cost pipeline. See
`finops/README.md` and ADR-011.


## Human-in-the-loop: stopping consequential actions, and routing every alert to one place

Everything above detects and measures. `human_in_the_loop/` is where a
consequential action actually gets stopped pending a person's sign-off,
and where every pipeline failure - not just agent behavior - is
severity-tiered and routed. Both the agent-side approval gate and the
pipeline-side exception handler route through one centralized,
single-place-to-configure notification destination. See
`human_in_the_loop/README.md` and ADR-012.


## Identity: who is the agent, actually, when it connects?

Everything above assumes an identity is already asking - `identity/`
is what actually creates one. The agent gets its own Databricks service
principal, distinct from any human's login, scoped only to
`gold.semantic`, so ADR-007's row filters and column masks have a real,
distinct subject to apply to for agent traffic, and so
`mcp_audit_logger.py`'s `caller_identity` field can finally distinguish
agent activity from a person's own manual queries. See
`identity/README.md` and ADR-013.


## Orchestration: what can a sub-agent inherit from its parent?

`identity/` establishes who the top-level agent is. `orchestration/`
governs what happens the moment that agent delegates part of a task to
a sub-agent: constrained delegation ensures a sub-agent can only ever
receive a strict subset of its parent's own access, enforced
structurally by a token-exchange function that refuses to issue a
broader-scoped token, not by asking the sub-agent to behave. See
`orchestration/README.md` and ADR-014.


## AI Gateway: the model-leg of traffic

`ai_gateway/` covers the one leg none of the other layers touch: the
actual outbound call from the agent to a language model provider,
separate from the MCP layer's agent-to-tool traffic. A single choke
point enforces per-feature daily budgets and basic content policy
before any call proceeds, and books actual cost afterward using the
same per-feature rollup pattern as `finops/`. See `ai_gateway/README.md`
and ADR-015.


## End-to-End Orchestrator: all layers, one request

`orchestrator/` chains every layer above into a single real request
path - identity, guardrails, the AI gateway, constrained delegation,
MCP-governed semantic-layer access, human-in-the-loop approval,
governed query execution, post-call guardrails, and audit/cost logging
- demonstrating the full control flow a real question would travel,
not just each layer in isolation. See `orchestrator/README.md` and
ADR-016.

## Governance Registry: one spreadsheet, checked against code

`governance_registry_check/` consolidates this project's access rules,
identities, and HIPAA/ISO 42001/NIST AI RMF mappings into a single
spreadsheet (`docs/governance/registry/governance_registry.xlsx`), then
checks that spreadsheet against what `governance_policies.sql` actually
implements, flagging drift in either direction. Verified against a real
introduced mismatch before being trusted. See
`governance_registry_check/README.md` and ADR-017.
