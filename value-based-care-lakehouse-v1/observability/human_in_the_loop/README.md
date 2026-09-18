# Human-in-the-Loop Layer

This folder is the enforcement and notification layer covering both
halves of this project: the agent/AI side (`approval_gate.py`) and the
lakehouse pipeline side (`pipeline_exception_handler.py`). Both route
through one centralized `notification_config.py`, so there is exactly
one place to update where alerts go - not one address hardcoded per
module. See ADR-012 in `docs/decisions/ADRs.md` for full design
reasoning and sources.

## The one place to configure notifications

`notification_config.py` holds `NOTIFY_EMAIL`, read from the
`HITL_NOTIFY_EMAIL` environment variable if set, otherwise a placeholder
default. Every other module in this project that sends a human-in-the-
loop notification imports this value rather than constructing its own -
update the environment variable once, and both the agent approval flow
and the pipeline exception flow redirect together. Optional Slack and
PagerDuty destinations are defined the same way, off by default.

## Agent/AI side: approval_gate.py

A four-tier risk model for consequential agent actions:

Tier 1, read-only lookups, auto-approve and proceed immediately. Tier
2, bounded and reversible writes, also auto-approve but are logged for
audit review. Tier 3, medium-risk actions, require human approval
within a one-hour SLA. Tier 4, high-risk or irreversible actions,
require human approval within a fifteen-minute SLA and are flagged
urgent.

`request_action()` is the single entry point every consequential agent
action must call before executing - a PENDING result means the calling
code must halt, not proceed. This project has no write-capable agent
tool today (every existing tool is a Tier 1 read-only semantic-layer
lookup, per ADR-006), so this gate is built ahead of need, ready for
the day a write-capable tool is added.

Run the demonstration:

    python3 observability/human_in_the_loop/simulate_approval_gate.py

Real output from that run, including a Tier 3 approval and a Tier 4
denial, is saved in `example_approval_gate_output.txt`.

## Pipeline side: pipeline_exception_handler.py

Reads dbt's own `run_results.json` artifact and classifies each test or
load failure by severity, based on which layer it hit. A staging-layer
test failure is LOW severity and is logged only. A Vault-layer test
failure is MEDIUM and notifies a human. Any Vault load failure, or any
failure in the Gold or semantic layer - the layers agents actually
query, per ADR-006 - is automatically HIGH severity and notifies a
human as urgent, since bad data there can reach an agent as a
confidently-reported number.

Run the demonstration:

    python3 observability/human_in_the_loop/simulate_pipeline_exceptions.py

Real output from that run, across all severity tiers, is saved in
`example_pipeline_exception_output.txt`.

## Files

- `notification_config.py` - the single centralized notification
  destination every other module here imports.
- `approval_gate.py` - risk-tiered approval gate for agent actions.
- `simulate_approval_gate.py` - runnable demonstration.
- `example_approval_gate_output.txt` - real output from that run.
- `pipeline_exception_handler.py` - severity-tiered exception handling
  for dbt/Data Vault pipeline failures.
- `simulate_pipeline_exceptions.py` - runnable demonstration.
- `example_pipeline_exception_output.txt` - real output from that run.
