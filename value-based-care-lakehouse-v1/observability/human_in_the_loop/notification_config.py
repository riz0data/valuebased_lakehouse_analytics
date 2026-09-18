"""
notification_config.py

The single source of truth for where human-in-the-loop notifications
and exception alerts go, across every layer of this project - the
agent/AI side (guardrails, evaluation) and the lakehouse pipeline side
(dbt runs, Data Vault loads) alike.

This exists so there is exactly one place to update an email address,
Slack webhook, or PagerDuty key - not one buried in each pipeline and
each agent tool. Every other module in this project imports
NOTIFY_EMAIL (or the other settings below) from here rather than
hardcoding a destination.

To change where alerts go: edit the values below, or - the recommended
approach for anything real - set the corresponding environment
variable, which overrides the default. See .env.example at the repo
root for the pattern this project already uses for other config.
"""

import os

# The one email address every notification in this project routes to.
# Override with the HITL_NOTIFY_EMAIL environment variable in any real
# deployment - never edit this file per-environment.
NOTIFY_EMAIL = os.environ.get("HITL_NOTIFY_EMAIL", "governance-alerts@example.com")

# Optional secondary channels - both off by default. Set the env var to
# enable; same one-place-to-configure principle as the email above.
SLACK_WEBHOOK_URL = os.environ.get("HITL_SLACK_WEBHOOK_URL", None)
PAGERDUTY_ROUTING_KEY = os.environ.get("HITL_PAGERDUTY_ROUTING_KEY", None)

# How long a Tier 3/4 approval request waits before it is itself
# escalated as overdue - see approval_gate.py. Kept here, not
# hardcoded in the gate logic, for the same single-place-to-tune reason.
APPROVAL_SLA_MINUTES = {
    "tier_3": 60,     # medium-risk: needs a response within an hour
    "tier_4": 15,      # high-risk / irreversible: needs a response fast
}
