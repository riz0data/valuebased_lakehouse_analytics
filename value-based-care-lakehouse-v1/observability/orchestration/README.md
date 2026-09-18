# Orchestration Layer

This folder covers what happens the moment a single agent isn't the
only actor anymore - when it delegates part of a task to a sub-agent.
It's the companion to `identity/` (ADR-013): identity establishes who
the top-level agent is and what it's scoped to; this layer governs what
a sub-agent is allowed to inherit from it. See ADR-014 in
`docs/decisions/ADRs.md` for full reasoning.

## The core principle: constrained delegation

A sub-agent can only ever receive a strict subset of its parent's own
access - never the same standing credential, and never more. This is
enforced structurally, not by instruction: `delegate()` in
`sub_agent_delegation.py` is a token-exchange function that checks a
requested scope against the parent's actual scope and refuses to issue
a token - raising `ScopeEscalationError` - if the request exceeds what
the parent itself holds. A misbehaving or manipulated sub-agent cannot
talk its way past this, because the check does not depend on the
sub-agent's own behavior at all.

Every issued delegation token also links back to the parent token that
authorized it, so `trace_delegation_chain()` can reconstruct the full
delegation history behind any sub-agent action - the same traceability
principle `mcp_audit_logger.py` already applies to individual tool
calls, extended to cover delegation itself.

## Where this sits relative to the rest of the governance stack

This models access at the catalog and schema level, matching how Unity
Catalog grants actually work - it does not duplicate row-level
restriction, which ADR-007's row filters and column masks already
handle beneath this layer.

## Run the demonstration

    python3 observability/orchestration/simulate_sub_agent_delegation.py

This runs three scenarios: a valid delegation to a narrower-scoped
sub-agent, a delegation attempt that tries to escalate beyond the
parent's own scope and is refused, and a two-hop delegation chain
traced back to the original top-level identity. Real output from that
run is saved in `example_delegation_output.txt`.

## Status

This project has exactly one agent identity today
(`svc-agent-semantic-layer`, see `identity/`) and no sub-agent
delegation in actual use. This is a reference implementation, built
ahead of need, so the pattern is already in place the day a sub-agent
is introduced, rather than bolted on afterward.

## Files

- `sub_agent_delegation.py` - the constrained-delegation token-exchange
  model and delegation-chain tracing.
- `simulate_sub_agent_delegation.py` - runnable demonstration.
- `example_delegation_output.txt` - real output from that run.
