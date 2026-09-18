"""
simulate_sub_agent_delegation.py

A runnable, dependency-free demonstration of sub_agent_delegation.py:
a valid delegation to a narrower-scoped sub-agent, a refused delegation
attempt that tries to escalate beyond the parent's own scope, and a
traced two-hop delegation chain back to the original top-level identity.

Run it directly: python3 simulate_sub_agent_delegation.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from observability.orchestration.sub_agent_delegation import (
    AgentScope, delegate, trace_delegation_chain, ScopeEscalationError,
)


def run_simulation():
    # The top-level agent's own scope, matching identity_policy.yaml:
    # select-only access to the semantic layer.
    top_level_scope = AgentScope(
        identity_name="svc-agent-semantic-layer",
        permissions=frozenset({
            ("gold", "semantic", "SELECT"),
        }),
    )
    print(f"Top-level agent identity: {top_level_scope.identity_name}")
    print(f"Top-level scope: {sorted(top_level_scope.permissions)}\n")

    # Scenario 1: valid delegation - sub-agent asks for a subset of the
    # parent's scope (same catalog/schema, same access level - a real
    # narrower case would restrict to specific metrics, omitted here
    # since AgentScope models catalog/schema/access, not row-level
    # detail - that finer restriction is exactly what ADR-007's row
    # filters already handle beneath this layer).
    print("Scenario 1: sub-agent requests exactly the parent's own scope, nothing more.")
    token_1 = delegate(
        parent_scope=top_level_scope,
        requested_permissions=frozenset({("gold", "semantic", "SELECT")}),
        sub_agent_identity="svc-agent-semantic-layer-subtask-metric-lookup",
        task_description="Look up Medical Loss Ratio for the current quarter",
    )
    print(f"  Delegation granted: {token_1.sub_agent_identity} (token {token_1.token_id})\n")

    # Scenario 2: invalid delegation - sub-agent asks for something the
    # parent itself does not hold. This must be refused, not merely
    # logged as a warning.
    print("Scenario 2: sub-agent requests access the parent does not have (write access to gold.governance).")
    try:
        delegate(
            parent_scope=top_level_scope,
            requested_permissions=frozenset({
                ("gold", "semantic", "SELECT"),
                ("gold", "governance", "MODIFY"),
            }),
            sub_agent_identity="svc-agent-semantic-layer-subtask-rogue",
            task_description="Attempt to modify a governance policy",
        )
        print("  ERROR: this should have been refused and was not.")
    except ScopeEscalationError as e:
        print(f"  Delegation refused, as required: {e}\n")

    # Scenario 3: a second hop - the first sub-agent delegates a
    # narrower slice again to a third identity, and we trace the whole
    # chain back to the original top-level agent.
    print("Scenario 3: a two-hop delegation chain, traced back to the original identity.")
    sub_scope = token_1.scope
    token_2 = delegate(
        parent_scope=sub_scope,
        requested_permissions=frozenset({("gold", "semantic", "SELECT")}),
        sub_agent_identity="svc-agent-semantic-layer-subtask-metric-lookup-formatter",
        task_description="Format the Medical Loss Ratio result for the user",
        parent_token_id=token_1.token_id,
    )
    chain = trace_delegation_chain(token_2.token_id)
    print(f"  Chain length: {len(chain)} hops")
    for i, hop in enumerate(chain):
        print(f"    hop {i}: {hop.parent_identity} -> {hop.sub_agent_identity} ({hop.task_description})")


if __name__ == "__main__":
    run_simulation()
