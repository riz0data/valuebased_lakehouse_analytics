# Architecture Specification

Placeholder. Will contain the full narrative architecture specification:
Bronze/Silver/Gold layer design, semantic layer approach, and the business
narrative connecting Payment Integrity, Risk Adjustment, and Clinical Quality
into a single value-based care data platform.


---

## Framework-Agnostic Positioning: This Is a Reference Architecture, Not a Framework

Everything under `observability/` (guardrails, evaluation, FinOps,
human-in-the-loop, identity, orchestration, and the AI gateway) is
deliberately implemented in plain Python with no agent framework
dependency - no LangGraph, no Databricks Agent Bricks, no CrewAI or
AutoGen. That is an intentional choice, not an oversight, and it is
worth being explicit about why, since both Agent Bricks and LangGraph
are real, credible platforms that overlap with parts of this design.

**Why not build directly on one of them?** Agent Bricks is described
by Databricks as the control plane for unified governance, management,
monitoring and observability across all AI agents in an enterprise,
largely through low-code tooling. LangGraph is a lower-level
orchestration library, and its own documentation states it is focused
on the underlying capabilities important for agent orchestration:
durable execution, streaming, human-in-the-loop, and more. Both are
legitimate choices for a production deployment. But if this project
were built directly on either one, a reviewer would mostly be looking
at configuration of someone else's platform. Building the governance
logic by hand - the identity model, the constrained-delegation check,
the budget enforcement, the risk-tiered approval gate - is what makes
the actual architectural decisions visible and inspectable in code,
rather than hidden inside a vendor's or framework's internals.

**Why this still matters for a real deployment.** The claim underlying
this whole repo is that these are not one-off scripts but a reference
architecture: a set of enforcement points and design decisions that
would need to exist regardless of which execution platform eventually
runs them. Two companion documents make that claim concrete rather than
asserted:

- `docs/governance/agent_bricks_mapping.md` walks through how each
  layer built here (identity, guardrails, evaluation, FinOps,
  human-in-the-loop, orchestration, AI gateway) would be realized on
  Databricks Agent Bricks specifically, and what Agent Bricks already
  provides natively versus what this repo's hand-built logic would
  still need to supply.
- `docs/governance/langgraph_mapping.md` does the same translation for
  LangGraph, where the mapping is especially direct: LangGraph's graph
  nodes, conditional edges, and interrupt-based human-in-the-loop
  primitive are a close structural match for this repo's approval
  gate and orchestration layer.

The intent is that a team already standardized on either platform
should be able to read this repo and see exactly where each governance
decision would be re-implemented using that platform's native
primitives, rather than needing to redesign the decisions themselves.
The hard part of this project was never the choice of framework - it
was deciding where enforcement needs to live, what a sub-agent should
never be allowed to inherit, and what should never proceed without a
human. Those decisions are portable; the execution substrate is not
the point.
