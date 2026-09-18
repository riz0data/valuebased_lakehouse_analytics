# Guardrails

Pre-call and post-call content checks for AI agent access to this
project's governed metrics, sitting at the same MCP proxy interception
point as the audit logger in `../mcp_audit_logger.py`. See ADR-010 in
`docs/decisions/ADRs.md` for the full design reasoning, and how this
differs from the reactive logging/alerting in `../` and the offline
scoring in `../evaluation/`.

**No agent is actually deployed against this project.** This is a
reference implementation, runnable and testable on its own.

## Files

- `guardrails.py` - two functions: `screen_input()` runs before a
  question reaches the model (checks for prompt injection and
  sensitive data patterns); `validate_output()` runs after the agent
  resolves a response, before it reaches the user (checks the claimed
  metric actually exists). Run directly: `python3 guardrails.py`.
- `example_guardrail_output.txt` - real, captured output from running
  the script: four pre-call examples (a clean question, an injection
  attempt, sensitive data needing redaction, and a system-prompt
  extraction attempt) and three post-call examples (a real metric, a
  legitimate no-match, and a hallucinated metric name), all correctly
  classified.

## Why this is different from everything else in `observability/`

Everything else here is reactive: the audit logger and alerting rules
(`../mcp_audit_logger.py`) notice a problem after a call completes, and
the evaluation harness (`../evaluation/`) scores correctness offline.
Guardrails are the one piece that acts *before* a bad request reaches
the model, and *before* a bad response reaches the user - prevention,
not just detection.

## Pre-call: `screen_input()`

Pattern-matches the raw question against explicit prompt-injection
phrasings ("ignore previous instructions," "reveal your system
prompt") and sensitive-data patterns (SSNs, emails, member-ID-shaped
strings). Returns one of three actions:

- **BLOCK** - suspected injection; the request should not proceed.
- **REDACT** - sensitive data found; the question still proceeds to the
  model, but with the sensitive substring masked first.
- **ALLOW** - clean.

Deliberately simple, explicit regex matching rather than a model-based
classifier - matches the real "deterministic input filter" pattern used
as the fastest, cheapest check in production guardrail stacks, run
before anything more expensive.

## Post-call: `validate_output()`

Checks whether the agent's claimed metric actually exists in
`dbt/models/semantic/_metrics.yml`. This reuses the exact same
schema-validity check as Layer 1 of the evaluation harness
(`../evaluation/evaluate_agent.py`) - one definition of "is this a real
metric" shared between the offline evaluation system and the live,
blocking guardrail, rather than two that could quietly drift apart.
BLOCKs a hallucinated metric name from ever reaching a user; ALLOWs a
real metric or a legitimate "no match" response.

## What this doesn't cover

Pattern-based injection detection catches known, explicit phrasings,
not novel or obfuscated attempts - a production deployment would likely
add a model-based classifier alongside this for the cases regex misses.
The sensitive-data patterns here are illustrative, not a complete PII
detection system. And this is a content-level check, not the primary
defense - the real access-control boundary is the Unity Catalog row
filters and column masks in `dbt/models/gold/governance_policies.sql`
(ADR-007) and the `DISABLE_SQL=true` default (ADR-006); guardrails add
a layer on top of that foundation, not a replacement for it.
