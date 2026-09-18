"""
sub_agent_delegation.py

Reference implementation of constrained delegation: the orchestration
pattern that ensures a sub-agent can never receive more access than its
parent agent had, only ever an equal or narrower slice. This is the
companion to observability/identity/ (ADR-013) - identity establishes
who the top-level agent is and what it's scoped to; this module governs
what happens the moment that agent delegates part of a task to another
agent.

Mechanism, in plain terms (see ADR-014 in docs/decisions/ADRs.md for
sources): the parent never hands its own credential to a sub-agent.
Instead, delegation is a token-exchange step - the parent requests a
new, narrower-scoped token for the specific sub-task, explicitly
listing which subset of its own scope the sub-agent needs. The
enforcement point is the exchange function itself: it is structurally
impossible to mint a sub-agent token with broader scope than the
parent's own, because the function refuses to issue one - not because
the sub-agent has been asked nicely not to exceed it.

Every delegation is logged with a parent-child link, so any sub-agent
action can be traced back through the full delegation chain to the
original top-level agent identity that started it - the same
traceability principle mcp_audit_logger.py already applies to
individual tool calls, extended to cover delegation itself.

This project has exactly one agent identity today
(svc-agent-semantic-layer, see identity/) and no sub-agent delegation
in actual use - this is a reference implementation, built ahead of
need, so the pattern is already in place the day a sub-agent is
introduced, rather than bolted on afterward.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AgentScope:
    """A concrete, checkable permission set - deliberately just a set
    of (catalog, schema, access_level) tuples, not a free-text
    description, so 'is B a subset of A' is a real, testable question
    rather than a matter of interpretation."""
    identity_name: str
    permissions: frozenset  # frozenset of (catalog, schema, access_level) tuples

    def is_subset_of(self, other: "AgentScope") -> bool:
        return self.permissions.issubset(other.permissions)


@dataclass
class DelegationToken:
    token_id: str
    issued_at_utc: str
    parent_identity: str
    sub_agent_identity: str
    scope: AgentScope
    task_description: str
    parent_token_id: Optional[str] = None  # chains delegation across more than one hop


# In a real deployment this would be a Delta table, same pattern as
# mcp_audit_logger.py's event log - kept in-memory here so this module
# is runnable standalone as a reference implementation.
_DELEGATION_LOG: list[DelegationToken] = []


class ScopeEscalationError(Exception):
    """Raised when a delegation request asks for more access than the
    parent identity actually has. This is the enforcement point - the
    exchange function refuses to issue the token; it does not rely on
    the sub-agent voluntarily staying within bounds."""
    pass


def delegate(parent_scope: AgentScope, requested_permissions: frozenset,
             sub_agent_identity: str, task_description: str,
             parent_token_id: Optional[str] = None) -> DelegationToken:
    """
    The single entry point a parent agent calls to spin up or delegate
    to a sub-agent. Requests a new, narrower-scoped token rather than
    handing over the parent's own credential. Raises
    ScopeEscalationError if the requested permissions are not a subset
    of what the parent itself holds - this is what makes escalation
    structurally impossible rather than merely discouraged.
    """
    requested_scope = AgentScope(identity_name=sub_agent_identity, permissions=requested_permissions)

    if not requested_scope.is_subset_of(parent_scope):
        excess = requested_permissions - parent_scope.permissions
        raise ScopeEscalationError(
            f"Delegation refused: '{sub_agent_identity}' requested permissions "
            f"the parent '{parent_scope.identity_name}' does not hold: {excess}. "
            f"A sub-agent can only ever receive a subset of its parent's scope."
        )

    token = DelegationToken(
        token_id=str(uuid.uuid4()),
        issued_at_utc=datetime.now(timezone.utc).isoformat(),
        parent_identity=parent_scope.identity_name,
        sub_agent_identity=sub_agent_identity,
        scope=requested_scope,
        task_description=task_description,
        parent_token_id=parent_token_id,
    )
    _DELEGATION_LOG.append(token)
    return token


def trace_delegation_chain(token_id: str) -> list[DelegationToken]:
    """
    Walks a delegation token back through every parent hop to the
    original top-level agent identity - the traceability half of this
    module. Given any sub-agent's token, answers "who ultimately
    authorized this, through how many hops."
    """
    chain = []
    lookup = {t.token_id: t for t in _DELEGATION_LOG}
    current = lookup.get(token_id)
    while current is not None:
        chain.append(current)
        current = lookup.get(current.parent_token_id) if current.parent_token_id else None
    return list(reversed(chain))


if __name__ == "__main__":
    print(
        "This module defines constrained delegation for sub-agent "
        "orchestration. Run simulate_sub_agent_delegation.py for a "
        "runnable, dependency-free demonstration of a valid narrower-"
        "scope delegation, a refused scope-escalation attempt, and a "
        "traced two-hop delegation chain."
    )
