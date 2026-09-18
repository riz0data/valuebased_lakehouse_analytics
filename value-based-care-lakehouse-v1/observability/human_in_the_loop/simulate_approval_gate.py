"""
simulate_approval_gate.py

A runnable, dependency-free demonstration of approval_gate.py's
risk-tiered enforcement: Tier 1 and Tier 2 auto-approve and proceed
immediately, Tier 3 and Tier 4 halt and require a human response before
anything is allowed to execute.

Run it directly: python3 simulate_approval_gate.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from observability.human_in_the_loop.approval_gate import (
    request_action, resolve_request, pending_requests, RiskTier, ApprovalStatus,
)


def run_simulation():
    print("Simulating four agent actions across all four risk tiers.\n")

    scenarios = [
        ("Look up Medical Loss Ratio for Q3", RiskTier.TIER_1_READ_ONLY),
        ("Write a cached result to the agent's own scratch table", RiskTier.TIER_2_BOUNDED_WRITE),
        ("Trigger a re-run of the Gold-layer dbt build", RiskTier.TIER_3_MEDIUM_RISK),
        ("Modify a governance_policies.sql row filter definition", RiskTier.TIER_4_HIGH_RISK),
    ]

    results = []
    for description, tier in scenarios:
        req = request_action(description, requested_by="agent:claude-desktop/rizwan", risk_tier=tier)
        results.append(req)
        outcome = "PROCEEDS IMMEDIATELY" if req.status == ApprovalStatus.AUTO_APPROVED else "BLOCKED - awaiting human approval"
        print(f"  [{tier.value}] '{description}'\n      -> {outcome}\n")

    print(f"Pending requests awaiting a human right now: {len(pending_requests())}")
    for p in pending_requests():
        print(f"  - {p.request_id} : {p.action_description} (SLA {p.sla_minutes} min)")

    print("\nSimulating a human approving the Tier 3 request and denying the Tier 4 request...\n")
    tier_3_req = [r for r in results if r.risk_tier == RiskTier.TIER_3_MEDIUM_RISK][0]
    tier_4_req = [r for r in results if r.risk_tier == RiskTier.TIER_4_HIGH_RISK][0]

    resolved_3 = resolve_request(tier_3_req.request_id, approved=True)
    resolved_4 = resolve_request(tier_4_req.request_id, approved=False)

    print(f"  Tier 3 request resolved: {resolved_3.status.value} -> pipeline may now proceed.")
    print(f"  Tier 4 request resolved: {resolved_4.status.value} -> action permanently blocked.")

    print(f"\nPending requests remaining: {len(pending_requests())}")


if __name__ == "__main__":
    run_simulation()
