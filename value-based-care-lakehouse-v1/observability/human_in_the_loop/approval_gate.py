"""
approval_gate.py

The human-in-the-loop approval gate for the agent/AI side of this
project - the enforcement point that sits between an agent deciding to
take a consequential action and that action actually running.

Design principle (see ADR-012 in docs/decisions/ADRs.md for sources):
real HITL is a risk-tiered architectural constraint, not a prompt
instruction. A prompt telling an agent "ask for approval before doing
X" is a suggestion the agent can ignore, misread, or be talked past by
a crafted input. This gate lives outside the model entirely - it is
plain Python that the calling code must pass through, so no prompt
injection reaching the agent can bypass it. This is the same
enforcement principle guardrails.py already applies to pre/post-call
screening; this module applies it to actions rather than content.

Risk tiering, deliberately narrow at the top:

  Tier 1 (read-only lookup)         - auto-approved, no human involved.
  Tier 2 (bounded write, reversible)- auto-approved, but logged for
                                       audit review after the fact.
  Tier 3 (medium-risk action)       - requires human approval, SLA-timed.
  Tier 4 (high-risk / irreversible) - requires human approval, tightest
                                       SLA, always escalated as P1 if it
                                       breaches SLA.

This project has no consequential write-capable agent action today -
every existing tool is a read-only semantic-layer lookup (ADR-006), so
every real call in this codebase is Tier 1. This module exists so that
the moment a write-capable or consequential tool is added, the gate is
already there rather than bolted on after the fact. See
example_approval_gate_output.txt for a runnable demonstration using
hypothetical Tier 3/4 actions to show the gate actually blocking
execution pending approval.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from observability.human_in_the_loop.notification_config import (
    NOTIFY_EMAIL,
    APPROVAL_SLA_MINUTES,
)


class RiskTier(Enum):
    TIER_1_READ_ONLY = "tier_1"
    TIER_2_BOUNDED_WRITE = "tier_2"
    TIER_3_MEDIUM_RISK = "tier_3"
    TIER_4_HIGH_RISK = "tier_4"


class ApprovalStatus(Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass
class ApprovalRequest:
    request_id: str
    timestamp_utc: str
    action_description: str
    requested_by: str          # e.g. "agent:claude-desktop/rizwan"
    risk_tier: RiskTier
    status: ApprovalStatus
    notify_email: str
    sla_minutes: Optional[int]


# In a real deployment this would be a Delta table
# (gold.observability.approval_requests), written and read the same
# way mcp_audit_logger.py logs events. Kept as an in-memory list here
# so this module is runnable standalone as a reference implementation.
_APPROVAL_LOG: list[ApprovalRequest] = []


def request_action(action_description: str, requested_by: str, risk_tier: RiskTier) -> ApprovalRequest:
    """
    The single entry point every consequential agent action must pass
    through before executing. Returns an ApprovalRequest whose status
    tells the caller whether it is safe to proceed:

      AUTO_APPROVED -> proceed immediately (Tier 1 and Tier 2).
      PENDING       -> DO NOT PROCEED. A human must approve first; the
                       calling code must halt and wait, or fail closed,
                       never assume approval and continue.

    This is the actual enforcement mechanism: any code that calls this
    and then executes on PENDING rather than halting has broken the
    gate, not the gate itself failing.
    """
    is_auto = risk_tier in (RiskTier.TIER_1_READ_ONLY, RiskTier.TIER_2_BOUNDED_WRITE)

    request = ApprovalRequest(
        request_id=str(uuid.uuid4()),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        action_description=action_description,
        requested_by=requested_by,
        risk_tier=risk_tier,
        status=ApprovalStatus.AUTO_APPROVED if is_auto else ApprovalStatus.PENDING,
        notify_email=NOTIFY_EMAIL,
        sla_minutes=APPROVAL_SLA_MINUTES.get(risk_tier.value),
    )

    _APPROVAL_LOG.append(request)

    if not is_auto:
        _send_approval_notification(request)

    return request


def _send_approval_notification(request: ApprovalRequest) -> None:
    """
    Sends the actual human-in-the-loop notification. Routes through the
    single centralized NOTIFY_EMAIL from notification_config.py - this
    is the one function in the whole project that should ever construct
    an outbound alert message for an approval request, so there is
    exactly one place to change the destination or the message format.

    Stand-in print statement here, same pattern as
    mcp_audit_logger.send_alert() - in a real deployment this is an
    actual email send (or Slack/PagerDuty via the optional channels in
    notification_config.py), not custom SMTP code written from scratch.
    """
    urgency = "URGENT - " if request.risk_tier == RiskTier.TIER_4_HIGH_RISK else ""
    print(
        f"[APPROVAL NEEDED - {urgency}{request.risk_tier.value}] "
        f"To: {request.notify_email} | "
        f"Action: '{request.action_description}' requested by {request.requested_by} | "
        f"SLA: {request.sla_minutes} minutes | Request ID: {request.request_id}"
    )


def resolve_request(request_id: str, approved: bool) -> Optional[ApprovalRequest]:
    """
    Called when a human actually responds to a pending request - the
    only function allowed to move a request out of PENDING. In a real
    deployment this would be triggered by a reply-to-approve email
    workflow or a small internal approval UI, not exposed as a raw API.
    """
    for req in _APPROVAL_LOG:
        if req.request_id == request_id and req.status == ApprovalStatus.PENDING:
            req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
            return req
    return None


def pending_requests() -> list[ApprovalRequest]:
    """Every request still awaiting a human response - the queue a real
    approval UI or scheduled SLA-breach check would read from."""
    return [r for r in _APPROVAL_LOG if r.status == ApprovalStatus.PENDING]


if __name__ == "__main__":
    print(
        "This module defines the human-in-the-loop approval gate for "
        "agent actions. Run example_approval_gate_output.txt's "
        "generating script (simulate_approval_gate.py) for a runnable, "
        "dependency-free demonstration of Tier 1 through Tier 4 "
        "requests, including a blocked Tier 4 action awaiting approval."
    )
