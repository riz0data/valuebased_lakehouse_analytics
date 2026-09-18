# Mapping This Architecture onto Databricks Agent Bricks

This document is the companion to the framework-agnostic positioning
section in `docs/architecture-spec.md`. It walks through, layer by
layer, how each hand-built module in `observability/` would be
realized if this project were deployed on Databricks Agent Bricks
instead of as plain Python, and is honest about what Agent Bricks
already provides natively versus what this repo's governance logic
would still need to supply.

Agent Bricks is Databricks' native agent platform: a control plane for
unified governance, management, monitoring and observability across all
AI agents in an enterprise, with low-code tooling (Agent Bricks Custom
Agents) for building the agents themselves, plus built-in automated
evaluation.

## Layer-by-layer mapping

**Identity (ADR-013).** This repo hand-builds a service-principal
identity and an explicit `identity_policy.yaml` declaring scope. On
Agent Bricks, this maps directly onto Databricks' existing Unity
Catalog service-principal model - Agent Bricks agents already run under
a Unity-Catalog-governed identity, since Agent Bricks is built on top
of the same Unity Catalog this repo's governance already assumes
(ADR-006, ADR-007). The identity mechanism is native; the specific
scope decision (semantic-layer-only, read-only) documented in
`identity_policy.yaml` is this project's own design choice and would
carry over unchanged as the actual Unity Catalog grant configuration.

**Guardrails (ADR-010).** This repo hand-builds pre-call and post-call
pattern checks in `guardrails.py`. Agent Bricks provides governance and
observability across all AI agents as a platform capability, and
Databricks' broader Mosaic AI stack includes guardrail and safety
tooling as part of its production agent framework. The specific
guardrail rules this project defined - the prompt-injection patterns,
the metric-hallucination check tied to `_metrics.yml` - are business
logic this repo owns either way; what changes is where that logic is
registered (a plain Python function here versus a guardrail
configuration or scoring function within Agent Bricks' evaluation
tooling).

**Evaluation (ADR-009).** This is the layer with the most direct native
overlap: Databricks' Agent Evaluation tooling was announced alongside
the Agent Bricks Custom Agents framework specifically to help
developers build and deploy high-quality agentic and RAG applications,
including automated evaluation. This repo's evaluation harness
(`observability/evaluation/`) would largely be replaced, not
translated, by Agent Bricks' native evaluation tooling in a real
Databricks-native deployment.

**FinOps - agent cost tracking (ADR-011).** This repo hand-builds
`agent_cost_tracker.py` because Databricks system tables have no
visibility into external LLM provider cost. Agent Bricks, since it runs
agents natively within the Databricks platform, changes this
significantly: agent calls made through Agent Bricks' own model
serving would actually appear in Databricks system billing tables,
closing the exact gap this repo's README calls out as the reason a
separate agent cost tracker is needed at all. This is a case where
platform-native deployment is a genuine improvement over what this
portfolio project can demonstrate standalone.

**Human-in-the-loop (ADR-012).** This repo hand-builds a risk-tiered
approval gate with a centralized notification config. LangGraph's own
documentation (see the companion LangGraph mapping doc) frames HITL as
a first-class orchestration primitive; Agent Bricks, as the governance
control plane across all AI agents in an enterprise, is the natural
place to configure approval policies platform-wide, but the specific
four-tier risk model and SLA structure this repo defines is this
project's own design decision, not something Agent Bricks prescribes -
it would need to be configured as an organization's own policy within
whatever approval hooks Agent Bricks exposes.

**Orchestration / constrained delegation (ADR-014).** This is the layer
Agent Bricks maps to least directly. Agent Bricks' governance is framed
around managing and monitoring agents an organization already has, not
a specific sub-agent-delegation permission model. The constrained-
delegation logic in `sub_agent_delegation.py` - the subset check, the
`ScopeEscalationError` enforcement, the delegation-chain tracing - is
this project's own architectural contribution and would need to be
built as custom logic regardless of platform, sitting alongside
whatever multi-agent coordination Agent Bricks provides natively.

**AI Gateway (ADR-015).** Also a layer this repo built to fill a gap
Agent Bricks does not fully own by itself - model routing, provider
budget, and content policy on the model-leg of traffic is a use case
served by dedicated AI gateway products (Envoy AI Gateway, LiteLLM,
Databricks' own Mosaic AI Gateway for model serving) rather than being
an Agent Bricks feature specifically. Databricks does offer its own
model-serving gateway capability as part of the broader Mosaic AI
platform, which this repo's `model_gateway.py` reference implementation
mirrors in miniature.

## Honest summary

Agent Bricks' strongest native overlap is identity (via Unity Catalog)
and evaluation, where this repo's hand-built logic would mostly be
replaced by platform features. Its weakest overlap is orchestration and
constrained delegation, and AI gateway routing, where this repo's
design decisions are genuinely this project's own contribution and
would need to be carried over as custom logic regardless of the
execution platform chosen.
