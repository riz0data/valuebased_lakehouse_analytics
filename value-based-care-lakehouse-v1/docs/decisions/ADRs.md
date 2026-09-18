# Architecture Decision Records

This document collects the key architectural decisions behind the Value-Based Care Lakehouse, each with its context, the decision made, and the trade-offs accepted.

---

# ADR-001: Data Vault 2.0 Over a Flat/Kimball-Only Model for the Silver Layer

## Status
Accepted

## Context

The Silver layer needs to integrate claims, enrollment, clinical, and pharmacy data arriving from multiple independent sources (CMS DE-SynPUF, Synthea, NPPES), each with its own grain, its own update cadence, and its own definition of shared entities like "member" and "provider." A traditional approach would land this data directly into a Kimball-style star schema at the Silver layer: conformed dimensions and fact tables, built once, updated in place.

That approach works well when source systems are stable and few. It becomes fragile here because:

- New sources need to be added over time (this project intentionally starts with three sources and is designed to accept more).
- Historical change needs to be preserved exactly as it was received, particularly for anything touching payment or risk score calculation, where an auditor or regulator may ask "what did we know, and when did we know it."
- Business keys (member ID, provider NPI, diagnosis code) need to be resolved and conformed across sources before any star schema can be built correctly.

## Decision

Model the Silver layer using Data Vault 2.0: Hubs for business keys, Links for relationships between business keys, and Satellites for descriptive, time-versioned attributes. The `automate_dv` dbt package generates these models from declarative YAML rather than hand-written SQL.

## Consequences

**Positive:**
- New source systems can be onboarded by adding new Satellites against existing Hubs, without reworking downstream models.
- Every attribute change is preserved with full history automatically, which is exactly the audit posture payment integrity and risk adjustment data need.
- Business keys are resolved once, in one place, rather than being re-resolved inconsistently in every downstream mart.

**Trade-offs:**
- The Silver layer has more tables and more joins than an equivalent Kimball model would, which adds real complexity and a steeper onboarding curve for engineers unfamiliar with the pattern.
- Query performance against raw Vault tables is worse than against a denormalized star schema. This is why the Gold layer still builds Kimball-style star schemas on top of the Vault - Data Vault is the system of record, not the consumption layer.

---

# ADR-002: Transactional Links for Financial and Clinical Events

## Status
Accepted

## Context

Several facts in this model are not descriptive attributes of an entity - they are discrete events that happened once and never change: a claim payment being issued, a claim adjustment being posted, a COB recovery being collected, a risk score being calculated for a member in a given model year, a quality measure being evaluated for a member in a given period.

Standard Data Vault 2.0 practice would model time-versioned descriptive data in a Satellite, which tracks changes to an entity's attributes over time. But payments, adjustments, and score calculations are not "changes to an entity" - they are immutable, independently occurring transactions, and a given member or claim can have many of them.

## Decision

Model these as Transactional Links (T-Links): claim payment transactions, claim adjustment transactions, COB recovery transactions, member risk score transactions, and member measure evaluation transactions are each modeled as their own T-Link, capturing the event, its business keys, and its measures at the moment it occurred, with no update-in-place ever performed.

## Consequences

**Positive:**
- Financial and clinical events are never overwritten, which preserves the exact audit trail regulators and auditors expect for claims and risk adjustment data.
- Multiple events of the same type for the same entity (a claim can be adjusted more than once, a member's risk score is recalculated every model year) are represented naturally, without awkward Satellite versioning logic.
- Aggregations like total leakage, YoY risk score trend, and cumulative recovery amounts become straightforward sums over T-Link rows rather than point-in-time snapshot logic.

**Trade-offs:**
- T-Links grow continuously and require partitioning and clustering strategy (this project uses Delta Lake Liquid Clustering) to keep query performance acceptable as event volume grows.
- Engineers need to correctly distinguish "this is a new fact about an existing thing" (Satellite) from "this is a new event that happened" (T-Link) when extending the model, which requires judgment rather than a mechanical rule.

---

# ADR-003: Conformed Hubs Shared Across Domains

## Status
Accepted

## Context

Payment Integrity, Risk Adjustment, and Clinical Quality are typically built as separate systems, each with its own definition of core entities like member, provider, and diagnosis. Payment Integrity might define "member" from claims data, Risk Adjustment from enrollment data, and Clinical Quality from encounter data - three definitions, three sets of identifiers, no reliable way to confirm they refer to the same underlying person.

This project's entire premise is that value-based care performance can only be measured by combining cost, risk, and quality for the same population at the same time. A metric like risk-adjusted shared savings rate requires knowing one member's cost, their risk score, and their quality outcomes simultaneously. That is structurally impossible if the three domains don't agree on who the member is.

## Decision

Core business entities - `hub_member`, `hub_provider`, `hub_diagnosis`, `hub_facility`, `hub_claim_line`, `hub_plan`, and `hub_employer_group` - are modeled once, as shared, conformed Hubs, keyed on a resolved business key. Every domain (Payment Integrity, Risk Adjustment, Clinical Quality, Pharmacy) attaches its own Links and Satellites to these same Hubs rather than creating domain-specific copies.

## Consequences

**Positive:**
- Cross-domain metrics (Net VBC Contract Value, Risk-Adjusted Shared Savings Rate) are simple joins across Links and Satellites hanging off the same Hub, rather than requiring a separate identity-resolution project.
- Adding a new domain later (for example, Utilization Management) means adding new Links and Satellites against existing Hubs, not rebuilding entity resolution from scratch.

**Trade-offs:**
- Business key resolution has to happen once, correctly, at the Hub level, which requires upfront design discipline before any domain-specific work can safely proceed.
- Changes to a conformed Hub's grain or key structure ripple across every domain that depends on it, so these Hubs need to be the most stable, most carefully reviewed part of the entire model.

---

# ADR-004: Open Data Sourcing - DE-SynPUF and Synthea Over Hand-Built Fake Data, HCPCS Over CPT

## Status
Accepted

## Context

This project needed realistic claims, clinical, provider, and drug data without using any real patient, member, or client-derived data. Two options existed: hand-write a synthetic data generator from scratch, or adopt existing, purpose-built open datasets.

Separately, procedure coding in U.S. healthcare typically uses CPT codes, but CPT is copyrighted and licensed by the American Medical Association, which makes it unsuitable for an open-source repository intended for unrestricted public use and forking.

## Decision

Use CMS DE-SynPUF for synthetic Medicare claims (explicitly published by CMS for this exact developer use case), Synthea for synthetic clinical/FHIR data (Apache 2.0, MITRE-maintained, widely adopted in the health IT community), and NPPES for real (but entirely public, non-PHI) provider directory data. Use HCPCS Level II instead of CPT for all procedure reference data, and use the public CMS Star Ratings measure set instead of licensed HEDIS technical specifications for quality measures.

## Consequences

**Positive:**
- Every dataset has a clear, verifiable, freely-checkable license, removing any ambiguity about whether the repository can be used, forked, or built upon without restriction.
- DE-SynPUF and Synthea are both widely recognized in the health data community, which lends credibility rather than requiring reviewers to trust an unfamiliar, hand-rolled generator.
- No party ever needs to ask "is this actually synthetic, or did you disguise real data" - the sourcing is independently verifiable.

**Trade-offs:**
- DE-SynPUF and Synthea were not designed to interoperate with each other, so meaningful engineering effort goes into aligning their identifiers and grains within the conformed Hub structure (see ADR-003).
- HCPCS Level II does not cover the full breadth of physician procedure coding that CPT does, so some real-world procedure detail is necessarily out of scope for this reference architecture.

## Amendment (Payment Integrity implementation)

In practice, `hub_procedure` is built from the ICD-9-CM procedure codes
present on DE-SynPUF Inpatient Claims (`ICD9_PRCDR_CD_1..6`), not HCPCS
Level II codes. DE-SynPUF's public release predates HCPCS-level
granularity, so no HCPCS data is actually present in the source file this
repository ingests - the original HCPCS-over-CPT decision above still
holds for *why* HCPCS was preferred over CPT, but no dataset used in this
repository currently supplies HCPCS codes at all. This substitution is
documented in `ingestion/payment_integrity/README.md` and flagged inline
in `hub_procedure.sql` rather than silently presented as HCPCS data.
Swapping in a real HCPCS-coded source (e.g. an Outpatient or Carrier
claims file, not yet ingested - see `ingestion/de_synpuf/README.md`)
would resolve this without changing the Vault structure.

---

# ADR-005: Semantic Layer Governance Over BI-Tool-Level Metric Definitions

## Status
Accepted

## Context

Metrics like leakage rate, RAF score, HCC capture rate, and Star Rating composite score are easy to define inconsistently: one analyst calculates leakage rate as a percentage of billed amount, another as a percentage of allowed amount, and both numbers get called "leakage rate" in different dashboards. This is exactly the kind of definitional drift that made the original three-domain problem hard to reason about in the first place.

The common alternative is to define these metrics inside the BI tool itself - as calculated fields in Tableau, Power BI, or Looker. That works until a second BI tool, a data science notebook, or an API consumer needs the same metric and has to reimplement the logic independently, with no guarantee it matches.

## Decision

Define every metric once, in the dbt Semantic Layer, as a governed metric object with an explicit calculation, explicit dimensions, and explicit row/column-level security. BI tools, notebooks, and any other consumer query the semantic layer rather than reimplementing metric logic locally.

## Consequences

**Positive:**
- A metric like Net VBC Contract Value has exactly one definition, one owner, and one place to fix it if the calculation needs to change.
- Row and column-level security (for example, restricting which providers a regional manager can see cost data for) is enforced centrally, rather than needing to be replicated in every downstream tool.
- New consumers (a new dashboard, a new analyst, a future ML model) inherit correct metric definitions automatically instead of needing to be taught the right formula.

**Trade-offs:**
- Every new metric requires a small amount of upfront governance overhead - it has to be defined in the semantic layer before it can be used anywhere, which is slightly slower than an analyst adding a quick calculated field directly in a dashboard.
- Consumers must have a query path to the semantic layer (via dbt's semantic layer API or a supported BI integration) rather than querying Gold tables directly, which is an adoption dependency for teams used to direct SQL access.


---

# ADR-006: AI Agent Access Through the Semantic Layer, Not Raw SQL

## Status
Accepted

## Context

ADR-005 established that every metric is defined once, centrally, in the dbt Semantic Layer, specifically so that BI tools, notebooks, and other consumers can't each reimplement "leakage rate" slightly differently. An AI agent querying this project's data is just another consumer, but it introduces a new failure mode the earlier decision didn't have to consider: an agent given raw SQL access can write a plausible-looking query against Gold or Vault tables that picks the wrong join, the wrong aggregation, or a subtly incorrect filter, and return a confident, wrong number with no way for the person reading it to know the calculation was never reviewed by anyone.

The dbt MCP server (Model Context Protocol server for dbt) is the mechanism this project uses to let an AI agent interact with the project at all. It ships with two categories of tools: Semantic Layer tools (`list_metrics`, `get_dimensions`, `query_metrics`) that only ever return numbers computed from the governed metric definitions in `dbt/models/semantic/_metrics.yml`, and raw SQL tools (`execute_sql`, `text_to_sql`) that let an agent write and run its own SQL directly against the warehouse.

## Decision

Configure the dbt MCP server for this project with `DISABLE_SQL=true`, which is also the tool's own default behavior, so an AI agent connected to this project can only query metrics through the governed Semantic Layer tools. Raw SQL access for an agent is not available out of the box, and turning it on requires a deliberate, separately-reviewed configuration change rather than being the default posture.

To make this workable in practice, every metric and dimension in `dbt/models/semantic/_metrics.yml` carries a `meta` block with a `domain`, a `unit`, a list of `synonyms`, and a `data_maturity` flag (`real_data` or `synthetic`). This is what lets an agent correctly match a loosely-phrased question, like "what's our risk score trend," to the right governed metric (`yoy_raf_score_trend`) instead of needing to write its own query from scratch to approximate an answer.

## Consequences

**Positive:**
- An AI agent's answers about business metrics are exactly as trustworthy as the governed Semantic Layer itself: if the agent picks the right metric, the number is guaranteed correct, because the underlying calculation was already reviewed once when the metric was defined, not re-derived per question.
- The same row and column-level security enforced at the Unity Catalog layer (see ADR-007) applies automatically to agent queries, since they still execute as the querying identity's warehouse credentials, with no separate "AI access" security model to maintain.
- Extending AI readiness to a new metric is the same work as adding any other governed metric, an entry in `_metrics.yml` with a description and a `meta` block, not a separate integration project.

**Trade-offs:**
- An agent cannot answer a question that falls outside what's been modeled as a metric or dimension - it cannot, for example, invent a novel cross-tabulation nobody defined in advance. That's treated as a feature here, not a limitation: the alternative is an agent silently approximating an answer with unreviewed SQL.
- Synonyms and metadata require upkeep as new metrics are added or as stakeholders start asking for a metric by a name not yet in its `synonyms` list.


---

# ADR-007: Row Filters and Column Masks at the Gold Layer via Unity Catalog

## Status
Accepted

## Context

ADR-005 centralized metric definitions in the Semantic Layer so every
consumer gets the same numbers. ADR-006 extended that so an AI agent
queries governed metrics rather than writing its own SQL. Neither
decision, on its own, controls who (or what identity, human or agent)
is allowed to see which individual rows and columns once a query
actually reaches the warehouse. A regional operations manager querying
`payment_leakage_rate` should see their own region's numbers, not every
region's; someone without a PHI-handling justification querying
`dim_member` shouldn't see exact birth dates or race codes just because
they have read access to the Gold schema at all.

Unity Catalog provides two mechanisms for this: table-level row filters
and column masks, applied directly to a table with `ALTER TABLE ... SET
ROW FILTER` / `SET MASK` and backed by a SQL or Python UDF; and newer
catalog-wide ABAC (attribute-based access control) policies that apply
a masking or filtering rule across every table carrying a matching tag,
without touching each table individually. ABAC is the better fit once a
rule needs to apply consistently across dozens of tables (for example,
"mask every column tagged `pii`"); table-level filters and masks are
the better fit for a small number of specific, reviewed rules on
specific tables, which is this project's current scale.

## Decision

Apply table-level row filters and column masks directly to Gold tables,
using SQL UDFs registered in Unity Catalog and Databricks group
membership checks (`is_member(...)`), rather than adopting ABAC
policies at this stage. Specifically, in
`dbt/models/gold/governance_policies.sql`:

- A row filter on `dim_provider`, keyed on `practice_state`, so a
  regional manager's Unity Catalog group membership determines which
  providers' rows they see; anyone outside a recognized regional group
  sees every row, matching the actual org chart where most roles are
  cross-regional.
- Column masks on `dim_member.birth_date` (generalized to birth year)
  and `dim_member.race_code` (withheld entirely) for anyone outside the
  `phi_reviewers` group.
- Column masks on `dim_provider.provider_first_name` and
  `provider_last_name` (reduced to an initial) for anyone outside the
  `credentialing_team` group, since every metric in this repository
  groups provider performance by NPI or provider key, never by name.

This file is a plain SQL script, not a dbt model - it registers
governance functions and binds them with `ALTER TABLE`, which produces
no table of its own and isn't part of the `dbt build` DAG. It's run
once (or re-run idempotently, since every `CREATE OR REPLACE FUNCTION`
and `ALTER TABLE ... SET MASK` is safe to reapply) against a real
Databricks workspace after the Gold tables it governs already exist.

## Consequences

**Positive:**
- Row and column-level security is enforced once, in the warehouse,
  for every consumer, human or agent, BI tool or Semantic Layer query -
  exactly the property ADR-006 depends on to say an AI agent's access
  is "no separate security model to maintain."
- The rules are visible and reviewable in version control as ordinary
  SQL, rather than being configured only through a UI with no diff
  history.
- Table-level filters and masks are simple to reason about for a
  project this size: one function, one `ALTER TABLE` statement, one
  clearly governed table.

**Trade-offs:**
- Table-level filters and masks don't follow joins: `fact_claim_payment`
  carries `provider_hk` but not `practice_state`, so the regional row
  filter applied to `dim_provider` does not automatically restrict
  `fact_claim_payment` rows. Achieving that would require either
  denormalizing `practice_state` onto the fact table so the same filter
  can bind there directly, or moving to an ABAC policy with a
  join-aware predicate - neither is implemented here, and this is
  called out explicitly in `dbt/models/gold/README.md` as a known gap
  rather than silently implied to be covered.
- This approach doesn't scale cleanly if the number of PII/PHI-adjacent
  columns or regionally-restricted tables grows much further - at that
  point, the "define once as an ABAC policy, apply by tag" approach
  referenced above would be the better trade, and this ADR would need
  revisiting.
- Group membership (`regional_manager_northeast`, `phi_reviewers`,
  `credentialing_team`, and so on) is assumed to already exist in the
  workspace's identity provider; this repository defines the policies
  that reference those groups but does not provision the groups
  themselves, since account and identity administration is out of
  scope for an open-source data model repository.



---

# ADR-008: Continuous Audit Logging and Alerting for AI Agent Tool Calls

## Status
Accepted

## Context

ADR-006 and ADR-007 make an AI agent's access to this project trustworthy
by construction: it can only query governed Semantic Layer metrics, and
those queries inherit Unity Catalog's row and column security
automatically. Neither decision, on its own, produces a record of what
actually happened, nor does anything notice when an agent starts
behaving badly - retrying a failing call in a loop, spiking in latency,
or failing at an unusually high rate - while it is still happening
rather than being discovered later by someone reading a log by hand.

Neither the Model Context Protocol itself nor the dbt-mcp server logs
tool calls or monitors behavior by default - MCP is a request/response
protocol between an agent and a tool server, with no built-in audit
trail. Two things need to be true for this to be real observability
rather than passive record-keeping: every tool call needs to be
captured as structured data close to real time, and that data needs to
be actively evaluated against rules that can catch a misbehaving agent
and alert someone, not just sit in a table waiting to be queried.
Industry practice draws a real distinction here: passive tools "surface
traces, record token usage, visualize execution paths, flag anomalies
after the fact," while active enforcement is what actually catches a
problem, like a stuck retry loop, while it is still in progress rather
than after a full trace has already been produced.

## Decision

Two cooperating pieces, both designed to run as scheduled Databricks
Jobs on a 1-minute cadence:

1. **`log_agent_activity_batch()`** buffers tool-call events (caller
   identity, the original question, tool name and arguments, which
   governed metric and `meta.synonyms` entry it resolved to, status,
   latency, rows returned) and appends each minute's batch to a Delta
   table, `gold.observability.agent_query_log`. This is a scheduled
   micro-batch write, not a continuously-running Structured Streaming
   query, since 1-minute freshness is exactly the kind of
   lenient-latency case Databricks' own documentation recommends
   handling with a one-time-trigger batch job rather than a persistent
   stream.

2. **`check_for_agent_anomalies()`** runs immediately after, reading the
   same table's most recent window and evaluating three explicit rules:
   error rate over 20 percent, the same tool call with identical
   arguments repeating 5 or more times (a stuck-loop signal), and p99
   latency exceeding 5 seconds. Any rule that trips writes a row to
   `gold.observability.agent_alerts` and fires a notification -
   in production, this is a one-line Databricks SQL Alert pointed at
   the alerts table, needing no custom notification code at all.

Both are reference implementations - there is no live agent deployed
against this project. `observability/mcp_audit_logger.py` contains the
real Databricks Job task functions, written to be dropped into an
actual workspace as-is. Because that file requires a live SparkSession
and Delta tables to execute, `observability/simulate_agent_session.py`
reimplements the identical event schema and the identical three alert
rules over a plain Python list, so the logic itself is runnable and
verifiable by anyone reading this repo, with no Databricks workspace
required. Running it produces two scenarios: a healthy session that
correctly does not trigger any alert, and a simulated stuck-loop session
that correctly trips all three rules at once - both captured verbatim
in `observability/example_simulation_output.txt`.

## Consequences

**Positive:**
- Detection happens close to real time (a 1-minute cadence) rather than
  requiring someone to notice a problem later by reading a static log,
  closing the gap between passive recording and active enforcement that
  ADR-008's context section calls out.
- The three alert rules are simple, explicit, and explainable - anyone
  reading this repo can see exactly why an alert fired, rather than
  trusting an opaque anomaly-detection model.
- Because the exact same event schema and rule logic exists in both the
  Databricks-native version and the dependency-free simulation, the
  design is verifiable without needing a live workspace, while still
  being a real, drop-in implementation for one.
- Alerting reuses Databricks SQL Alerts rather than inventing a custom
  notification system, keeping the operational surface area small.

**Trade-offs:**
- A 1-minute cadence is a batch job, not true real-time streaming -
  an agent could complete a large burst of problematic calls within a
  single 1-minute window before the next scheduled run evaluates them.
  For this project's scale and purpose, that lag is an acceptable
  trade-off against the operational simplicity of a scheduled job over
  a persistent streaming pipeline.
- The three rules are fixed thresholds, not a learned or adaptive
  anomaly model - they will need tuning against real traffic patterns
  once an agent is actually deployed, and a single burst just under a
  threshold (for example, exactly 4 identical repeated calls) will not
  trigger, which is a known and accepted limitation of static
  thresholds over adaptive detection.
- This still does not include cost/token telemetry, drift detection, or
  hallucination scoring - it covers reliability signals (errors,
  loops, latency), not answer-quality signals, which would need a
  separate evaluation harness layered on top.


---

# ADR-009: Layered Evaluation for AI Agent Metric Resolution

## Status
Accepted

## Context

ADR-008 gives this project continuous audit logging and alerting for
agent *reliability* - errors, stuck loops, latency. It deliberately does
not evaluate agent *correctness*: an agent can return a fast, successful,
confidently-formatted response that simply resolved to the wrong
metric, and ADR-008's rules would show that as a perfectly healthy call.
Catching that requires a different kind of check, evaluated against
known-correct answers, not against error codes.

The obvious first instinct - and the one this project's design
discussion started with - is a single golden dataset of known-answer
test questions, run whenever metric definitions change. That is a real
and useful technique, but treating it as the *only* layer would
understate how the industry actually approaches this problem. Current
practice treats agent evaluation as multiple cooperating layers, not
one method: fast deterministic checks that need no model at all, golden
dataset regression tests for exact-match correctness, and judge-based
rubric scoring (traditionally a second LLM acting as a grader) for
softer qualities a simple pass/fail can't capture, run online against a
sample of real traffic rather than only offline before a release.

## Decision

Implement all three layers in `observability/evaluation/`, scoped
honestly to a project with no live agent deployed yet:

1. **Layer 1, deterministic checks** (`layer1_schema_check`): near-zero
   cost, no model involved. Does the agent's claimed metric actually
   exist in `_metrics.yml`? This catches a hallucinated metric name
   before any more expensive check runs at all.

2. **Layer 2, golden dataset regression testing**
   (`golden_dataset.json`, `layer2_exact_match`): a fixed set of test
   questions generated directly from the real `meta.synonyms` entries
   already defined for every metric, each with a known-correct expected
   metric. Exact match, pass or fail. Includes two adversarial cases on
   purpose: one legitimate "no match" (Medical Loss Ratio, a documented
   Data Gap) and one deliberately loose phrasing that doesn't literally
   contain a defined synonym, to keep the dataset honest about where
   synonym-matching actually breaks down rather than only including
   cases designed to pass.

3. **Layer 3, rubric-based scoring** (`layer3_rubric_score`): for cases
   that fail exact match, scores how *close* the miss was - same domain
   as the correct answer scores partial credit, a completely unrelated
   domain or a confident wrong answer where "no match" was correct
   scores zero. This reference implementation is a deterministic
   rubric function with the exact same inputs and outputs a real
   LLM-as-judge call would have, specifically so it runs with no API
   key or network dependency; in production, this function's body is
   what gets replaced with a call to a frontier model (or a small
   fine-tuned judge model for lower latency and cost at scale), sampled
   across live traffic rather than run only offline.

Because there is no live agent deployed against this project,
`simulated_agent_resolve()` stands in for a real agent's metric
resolution step, using simple synonym substring-matching. Running
`evaluate_agent.py` end-to-end today produces real, captured output
(`example_eval_run_output.txt`): 27 of 28 golden cases pass, and the one
genuine failure is the deliberately adversarial loose-phrasing case,
included specifically to demonstrate a real, honest limitation rather
than a curated all-green result.

## Consequences

**Positive:**
- Correctness evaluation is layered by cost, matching real practice:
  free deterministic checks run first and catch the cheapest class of
  error, exact-match regression testing catches known-metric drift, and
  rubric scoring catches partial-credit nuance a binary pass/fail would
  discard entirely.
- The golden dataset is generated directly from `_metrics.yml`'s own
  `meta.synonyms` field, so it can be regenerated automatically whenever
  a metric's synonyms change, rather than drifting out of sync as a
  hand-maintained fixture.
- Including a genuine, honestly-labeled failure case in the dataset
  (rather than only cases the harness is known to pass) demonstrates
  the evaluation's actual discriminating power, not just its existence.
- The rubric function's interface is deliberately identical to what a
  real LLM-as-judge call would look like, so swapping in a real model
  call later is a localized change, not a redesign.

**Trade-offs:**
- `simulated_agent_resolve()` is a simple substring matcher, not a real
  agent - it will need to be replaced with an actual call to the
  deployed agent (or directly to dbt-mcp's `list_metrics`) the moment
  one exists, and real agent behavior may reveal failure modes this
  stand-in can't produce.
- The Layer 3 rubric is a fixed, hand-written function, not a real
  model call - it cannot judge nuance outside the three cases it
  explicitly encodes (correct, same-domain miss, unrelated miss). A
  production deployment gets meaningfully more evaluative power from a
  real judge model at the cost of latency, spend, and the need to
  periodically re-align the judge against human-labeled examples.
- This evaluates metric *resolution* correctness only - it does not
  evaluate whether the underlying number returned by `query_metrics`
  is itself correct, since that correctness is already guaranteed by
  construction per ADR-006 (the Semantic Layer, not the agent,
  computes the number).


---

# ADR-010: Pre-Call and Post-Call Guardrails for AI Agent Tool Calls

## Status
Accepted

## Context

ADR-008 and ADR-009 are both reactive: the audit logger and alerting
rules notice a problem after a tool call completes (or after a minute
of traffic accumulates), and the evaluation harness scores correctness
offline, against a fixed dataset or sampled traffic. Neither one stops
a bad request before it reaches the model, or a bad response before it
reaches the user - both only ever observe and score after the fact.

Industry practice draws a clear line between two categories of runtime
check that sit in front of, not behind, the model call: pre-LLM
guardrails run before input reaches the model, screening for prompt
injection and sensitive data before any inference happens, while
post-LLM guardrails run after the model responds but before the
response reaches the user, catching hallucinations and invalid output.
There is also a broader, separate category worth naming explicitly:
agent security wraps the whole tool-using loop and governs what the
system is allowed to *do*, not just what it says, and real incidents
have consistently exploited that loop rather than tripping a content
filter. This project already addresses that broader category
elsewhere - ADR-007's Unity Catalog row filters and column masks are a
genuine permission boundary on what an agent (or anyone) can access,
and ADR-006's `DISABLE_SQL=true` bounds what actions are even possible
in the first place. What remains open is narrower: the content-level
checks immediately before and after a single model call.

## Decision

Add `observability/guardrails/guardrails.py`, two functions matching
the pre-LLM / post-LLM pattern, meant to run at the same MCP proxy
interception point as the audit logger in `mcp_audit_logger.py`:

- **`screen_input()`** (pre-call): pattern-matches the user's question
  against a small, explicit set of prompt-injection phrasings (for
  example, "ignore previous instructions," "reveal your system
  prompt") and sensitive-data patterns (SSNs, email addresses,
  member-ID-shaped strings typed directly into a question). Returns
  BLOCK for suspected injection, REDACT for sensitive data (masking it
  before the question proceeds to the model), or ALLOW otherwise.
- **`validate_output()`** (post-call): checks whether the agent's
  claimed metric actually exists in `_metrics.yml`, reusing the same
  schema-validity check as Layer 1 of the evaluation harness
  (`evaluate_agent.py`) - the same check is useful both as an offline
  evaluation metric and as a live, blocking guardrail. BLOCKs a
  hallucinated metric name from ever reaching a user; ALLOWs a real
  metric or a legitimate "no match."

Every guardrail decision returns an explicit action and a
human-readable reason rather than silently passing or failing, so a
BLOCK or REDACT is itself something the audit logger records, not an
invisible side effect. Deliberately simple, explicit pattern matching
is used for the pre-call check rather than a model-based classifier,
matching the real "deterministic input filter" layer used as the
cheapest, fastest check in production guardrail stacks, run before any
more expensive check.

This is a reference implementation, not a running service - there is no
live agent deployed against this project. Running
`guardrails.py` directly demonstrates both checkpoints against four
realistic pre-call examples and three realistic post-call examples, all
correctly classified, captured in `example_guardrail_output.txt`.

## Consequences

**Positive:**
- Bad input and bad output are stopped before they take effect, closing
  the gap ADR-008 and ADR-009 explicitly leave open: reactive detection
  after the fact versus prevention in the moment.
- Reusing the same metric-existence check between the evaluation
  harness and the live guardrail keeps the two systems consistent by
  construction - there's one definition of "is this a real metric,"
  not two that could drift apart.
- REDACT-before-block for sensitive data (rather than blocking the
  whole request outright) keeps the system usable: a question with an
  accidental member ID pasted in still gets answered, just without that
  identifier ever reaching the model.

**Trade-offs:**
- Pattern-based injection detection is inherently incomplete - it
  catches known, explicit phrasings, not novel or obfuscated injection
  attempts. A production deployment would likely add a model-based
  classifier as a second pre-call layer for the cases explicit patterns
  miss, at added latency and cost.
- The sensitive-data patterns here are illustrative, not a complete PII
  detection system - a real deployment handling genuine PHI would need
  a much more thorough entity-recognition approach, not three regular
  expressions.
- This does not replace the broader agent-security boundary already
  established by ADR-006 and ADR-007 - it adds content-level screening
  on top of an access-control foundation that was already sound, rather
  than being the primary defense on its own.


## ADR-011: FinOps Layer - Lakehouse Compute Cost and Agent/AI Cost Attribution

**Status:** Accepted

**Context:**

This project's observability layer (ADR-008) tracks agent behavior -
error rates, latency, repeated calls - but not cost. As this portfolio
demonstrates AI-agent access to a data platform, a complete story needs
a FinOps layer: where does money actually go, and can it be attributed
back to a project, team, or feature. This has two genuinely different
halves, because the cost mechanisms are unrelated:

1. Lakehouse compute cost - clusters, jobs, SQL warehouses running on
   Databricks, billed in DBUs.
2. Agent/AI cost - LLM API calls, billed per token by the model
   provider, with no relationship to Databricks compute billing at all.

**Decision:**

For lakehouse compute cost, attribute cost using Databricks' own
system tables rather than estimating it: join `system.billing.usage`
(real DBU consumption, already broken out by the custom tags attached
to each cluster/job/warehouse) against `system.billing.list_prices`
(the published dollar rate per DBU per SKU). This is the same real,
documented Databricks pattern used for production chargeback reporting
- no invented pricing model, no hand-estimated DBU-to-dollar
conversion. See `observability/finops/lakehouse_cost_attribution.sql`.

For agent/AI cost, attribute cost at the point of the call, since no
billing system table sees LLM API spend. Extend the existing
`ToolCallEvent` audit log (ADR-008) with a sibling `AgentCostEvent`
carrying token counts (read directly from the provider's response) and
a feature tag, and convert to dollars via a maintained per-model rate
lookup table. This rides on the audit log this project already has
rather than building a second, disconnected logging pipeline. See
`observability/finops/agent_cost_tracker.py`.

**Consequences:**

- Both halves are reference implementations, not running services -
  there is no live Databricks workspace or deployed agent in this
  portfolio project. Both are written to be dropped into a real
  environment as-is, with a runnable local simulation
  (`simulate_agent_cost.py`) and illustrative example output for
  the SQL side, since a live system-table query can't be captured here.
- The per-model rate lookup table in `agent_cost_tracker.py` is a
  manual maintenance point - rates change, and a stale rate silently
  understates real spend. A real deployment should source rates from
  provider billing APIs where available rather than a hardcoded table.
- Token cost is a necessary but partial view of real agentic cost.
  Retries, multi-step tool chains, and orchestration overhead are real
  cost drivers this module does not model - flagged explicitly rather
  than implied as covered, consistent with how ADR-007 and ADR-009
  name their own gaps.
- Tagging is the single point of failure for both halves: an untagged
  cluster or an agent call missing a feature tag becomes unattributable
  spend. `lakehouse_cost_attribution.sql` includes an explicit untagged-
  spend query for exactly this reason.


## ADR-012: Centralized Human-in-the-Loop Approval and Exception Handling

**Status:** Accepted

**Context:**

Prior ADRs built reactive detection - observability (ADR-008) detects
anomalies after the fact, guardrails (ADR-010) screen content before
and after a call. None of them stop a consequential action from
running, or route pipeline failures to a person, and none of them share
a single configurable destination for where a human actually gets
notified. As this project grows agent capability (FinOps, evaluation)
and pipeline complexity (Data Vault loads, Gold-layer builds), both the
agent side and the pipeline side need a real human-in-the-loop layer -
and specifically, one shared notification destination rather than each
piece hardcoding its own.

Real practice (see sources below) is risk-tiered, not blanket,
approval: gating every action on human sign-off trains reviewers to
rubber-stamp, and the one approval that actually matters gets the same
reflexive yes as a harmless lookup. The enforcement point also has to
live outside the model - a prompt instruction telling an agent to ask
first is a suggestion it can be talked past; a real gate is
architectural code the calling system must pass through.

**Decision:**

Build one centralized `notification_config.py` holding a single
`NOTIFY_EMAIL` (overridable via environment variable, never hardcoded
per-call), which every other module in this layer imports rather than
constructing its own destination. On top of that, build two enforcement
points that both route through it:

1. `approval_gate.py` - agent/AI side. A four-tier risk model (read-only
   auto-approved, bounded-write auto-approved-but-logged, medium-risk
   requires approval with a one-hour SLA, high-risk/irreversible
   requires approval with a fifteen-minute SLA). `request_action()` is
   the single entry point every consequential agent action must call;
   returning PENDING means the calling code must halt, not proceed.
2. `pipeline_exception_handler.py` - lakehouse pipeline side. Reads
   dbt's own `run_results.json` (no custom test framework invented)
   and classifies each failure's severity based on which model layer it
   hit - anything reaching the Gold or semantic layer (agent-queryable,
   per ADR-006) or any Vault load failure is automatically HIGH,
   because bad data there can reach an agent as a confidently-reported
   number. Low-severity staging failures are logged but do not page
   anyone, to keep the notification signal meaningful.

**Consequences:**

- There is now exactly one place to change where every alert in this
  project goes - both halves import `NOTIFY_EMAIL` from the same file,
  so updating one environment variable redirects agent approval
  requests and pipeline exceptions alike.
- This project has no write-capable or consequential agent action
  today - every existing tool is a Tier 1 read-only semantic-layer
  lookup. `approval_gate.py` is therefore a reference implementation
  built ahead of need, not something exercised by real traffic yet;
  it exists so a future write-capable tool has the gate already in
  place rather than bolted on after the fact.
- Both `_send_approval_notification()` and
  `_send_exception_notification()` are stand-in print statements, same
  pattern as `mcp_audit_logger.send_alert()` - a real deployment wires
  these to an actual email send or the optional Slack/PagerDuty
  channels already present in `notification_config.py`.
- The severity tiering in `pipeline_exception_handler.py` is
  deliberately simple and explicit, not a learned model, for the same
  reason ADR-008's alert thresholds are - anyone reading the code can
  see exactly why a failure did or didn't escalate.
- Sources: real-world 2026 guidance on risk-tiered human-in-the-loop
  design for AI agents, emphasizing that over-gating trains rubber-
  stamping and that the enforcement point must sit outside the model
  itself, informed this design; see web search citations in this
  session's transcript.


## ADR-013: A Distinct Non-Human Identity for the Agent, Separate From Any Human User

**Status:** Accepted

**Context:**

ADR-006 decided agents only access data through the governed semantic
layer, and ADR-007 built row filters and column masks that apply
"per identity." Neither ADR ever specified what identity an agent
actually authenticates as at runtime. In this project's current setup,
an agent connecting via the dbt-mcp server authenticates using whatever
personal Databricks credential the developer supplies in `.env`, which
means agent-originated queries and a human's own manual queries are
indistinguishable to Unity Catalog and to the audit log - both see the
same identity. This breaks two things already built: ADR-007's per-
identity policies can't actually apply differently to agent traffic
versus human traffic if there's only one identity to apply them to, and
`mcp_audit_logger.py`'s `caller_identity` field can't genuinely
distinguish agent activity from human activity in review.

Real 2026 practice treats an agent as its own non-human identity with
its own short-lived, individually-scoped credential - not a shared
secret, and never a standing personal token repurposed for automated
use. Constrained delegation is the parallel principle for orchestration
(a sub-agent can only ever receive a subset of its parent's privileges,
never more) but that's a separate, not-yet-built concern - see the
Consequences section below.

**Decision:**

Give the agent its own Databricks Unity Catalog service principal,
`svc-agent-semantic-layer`, distinct from any individual human's login:

- `observability/identity/create_agent_service_principal.sql` grants
  that service principal `SELECT` on `gold.semantic` only - nothing on
  any other Gold schema, and nothing on staging or vault, consistent
  with ADR-006's original semantic-layer-only scope.
- `observability/identity/identity_policy.yaml` documents the identity,
  its credential mechanism (short-lived OAuth, never a static personal
  access token), and its exact allowed and explicitly denied scope, as
  reviewable data rather than scattered comments.
- `.env.example` and `.mcp/mcp.json.example` are updated to make
  explicit that `DBT_TOKEN` must be this service principal's OAuth
  credential, never the developer's own personal token - the agent's
  credential surface is now documented as distinct from the human
  administrator's.

**Consequences:**

- Unity Catalog service principals are account-level objects created
  via the account console or Terraform, not via SQL - the `.sql` file
  here is the grants step only, assuming the identity already exists;
  see the folder's README for the one-time console setup step this
  project cannot script from a repo alone.
- ADR-007's row filters and column masks now have a real, distinct
  subject to apply to for agent traffic specifically - this ADR is
  what makes those policies mean something for the agent, not a
  replacement for them.
- `mcp_audit_logger.py`'s `caller_identity` field should now be
  populated with this service principal's name for agent-originated
  events, making agent activity distinguishable from human activity in
  the audit log for the first time - the audit logger's code does not
  need to change, only what value flows into that field at call time.
- This is a reference implementation - there is no live Unity Catalog
  metastore or deployed agent in this portfolio project, so the service
  principal, grants, and credential separation described here are
  documented and ready to apply, not exercised against real traffic.
- Orchestration - what happens when this agent delegates to a sub-agent,
  and how constrained delegation would scope a sub-agent to strictly
  less access than its parent - is a related but distinct concern, not
  addressed by this ADR, since this project has exactly one agent
  identity and no sub-agent delegation today.


## ADR-014: Constrained Delegation for Sub-Agent Orchestration

**Status:** Accepted

**Context:**

ADR-013 gave the agent its own identity, distinct from any human, with
a defined scope. That covers a single agent acting alone. The moment
that agent delegates part of a task to a sub-agent - a common pattern
as agent workflows grow (multi-step lookups, specialized helper agents)
- a new risk appears: nothing so far stops a sub-agent from being
handed the same access as its parent, or worse, more than its parent
had, if delegation is done carelessly. Real 2026 guidance on this
(see ADR-013's sources, which cover the same body of practice) is
explicit that constrained delegation - a sub-agent receiving only a
strict subset of its parent's privileges, never more - is the
architectural answer, enforced structurally rather than by asking the
sub-agent nicely to stay in bounds.

**Decision:**

Build `observability/orchestration/sub_agent_delegation.py` as a
token-exchange model: a parent agent never hands its own credential to
a sub-agent. Instead, `delegate()` is the single entry point a parent
calls, requesting a new, explicitly narrower-scoped token for a
specific sub-task. The function checks the requested scope against the
parent's own scope using a real, testable subset check
(`AgentScope.is_subset_of()`, over a concrete set of catalog/schema/
access-level permissions, not a free-text description) and raises
`ScopeEscalationError`, refusing to issue the token, if the request
exceeds what the parent itself holds. Every issued token also carries
an optional link to the parent token that authorized it, so
`trace_delegation_chain()` can walk any sub-agent's token back through
every hop to the original top-level identity.

**Consequences:**

- Escalation is structurally impossible, not merely discouraged: the
  refusal happens inside `delegate()` itself, the same enforcement-
  outside-the-model principle `approval_gate.py` (ADR-012) already
  applies to consequential actions - a sub-agent cannot talk its way
  into broader access because the exchange function does not depend on
  the sub-agent's own behavior at all.
- This project has exactly one agent identity today
  (`svc-agent-semantic-layer`, ADR-013) and no sub-agent delegation in
  actual use - this is a reference implementation, built ahead of need,
  demonstrated in `simulate_sub_agent_delegation.py` against
  hypothetical sub-agents rather than real traffic.
- `AgentScope` models access at the catalog/schema/access-level
  granularity, matching how Unity Catalog grants work. It does not
  model row-level restriction - that finer-grained control is already
  handled beneath this layer by ADR-007's row filters and column masks,
  which this module does not duplicate.
- The in-memory `_DELEGATION_LOG` is a stand-in for a Delta table, same
  pattern as `mcp_audit_logger.py`'s event log - a real deployment
  would persist delegation tokens the same way, so a delegation chain
  can be traced during a real incident review, not just within a single
  process's lifetime.


## ADR-015: AI Gateway for Model-Leg Traffic

**Status:** Accepted

**Context:**

Every layer built so far governs either the lakehouse side (Unity
Catalog policies, observability, FinOps for compute) or the
agent-to-tool leg of agentic traffic (ADR-006's semantic-layer-only
rule, the MCP config, identity, delegation). None of it governs the
agent-to-model leg specifically - the actual outbound call to a
language model provider. That leg has its own distinct failure modes:
provider outages, rate limits, and quota breaches, handled with routing
and budgets, which are a different concern from MCP's tool-level
failure modes such as tool poisoning or confused-deputy attacks. Real
AI gateway products exist precisely to centralize this leg: an AI
gateway sits between your applications and your LLMs, agentic AI and
AI agents, orchestrating requests and enforcing policies, and it
differs from a regular API gateway because it is built specifically
for AI workloads.

**Decision:**

Build `observability/ai_gateway/model_gateway.py` as a single choke
point every model call passes through, structured the way real
gateways are: a control plane of policy/budget/routing rules
(`PROVIDER_RATES_PER_1K_TOKENS`, `DAILY_BUDGET_USD_BY_FEATURE`,
`DENIED_CONTENT_MARKERS`) separated from a data plane
(`route_request()` / `record_response()`) that actually books usage.
`route_request()` is called before any model call proceeds and refuses
the call - raising `BudgetExceededError` or `ContentPolicyError` - if
it would exceed the calling feature's daily budget or contains a
disallowed content pattern. `record_response()` re-runs the content
check on the response side, since a gateway inspects both legs of the
conversation, not only the outbound prompt, then books the actual cost
against the same per-feature spend ledger pattern already used in
`observability/finops/agent_cost_tracker.py`.

**Consequences:**

- This is explicitly not a replacement for the MCP layer already in
  place. MCP governs how the agent reaches tools and the semantic
  layer; this gateway governs only the separate leg where the agent
  calls a model. Both layers now exist, each scoped to the traffic it
  actually governs, rather than one trying to cover both.
- The reference implementation uses a single mocked provider with no
  real network calls or API keys, sized to demonstrate the pattern
  (split control plane and data plane, budget enforcement, basic
  content policy) rather than to be production-ready multi-provider
  routing - a real deployment would add actual provider failover, a
  proper PII/content-safety classifier in place of the current
  substring check, and persistent storage for the spend ledger instead
  of the in-memory dictionary used here.
- Enforcement happens inside `route_request()` itself and does not
  depend on the calling agent behaving - the same enforce-outside-the-
  model principle already applied in `approval_gate.py` (ADR-012) and
  `sub_agent_delegation.py` (ADR-014).


## ADR-016: End-to-End Orchestrator Chaining All Agentic AI Layers

**Status:** Accepted

**Context:**

Every layer built across this project (guardrails, evaluation, FinOps,
identity, human-in-the-loop, orchestration/delegation, and the AI
gateway) has been built and demonstrated independently, each with its
own simulation script. That proves each layer works in isolation, but
it does not show how a single real request actually flows through all
of them together, in order, which is the more honest picture of what
"the architecture" means in practice.

**Decision:**

Build `observability/orchestrator/end_to_end_orchestrator.py` as a
single reference request path: identity tagging, pre-call guardrails,
the AI gateway's model-leg check, constrained delegation to a sub-agent,
the MCP-governed semantic-layer access check, the human-in-the-loop
approval gate, governed query execution (represented, not live, since
Unity Catalog row filters/column masks per ADR-007 aren't re-simulated
here), post-call guardrails, audit and cost logging, and a final
plain-language summary. Every enforcement point is real code from the
actual modules already built - this file does not reimplement any of
them, it imports and calls them in sequence. Where a step would call a
real language model or run a live SQL query, it is represented with a
clearly labeled mock rather than invented as if it were live, consistent
with every other module's "reference implementation" framing.

**Consequences:**

- `simulate_end_to_end.py` demonstrates three real outcomes: a full
  successful run that touches all nine enforcement points and returns a
  correct governed-metric answer, a run halted at guardrails by a
  genuine prompt-injection pattern before the model is ever called, and
  a run halted at the human-in-the-loop gate pending approval for a
  higher-risk hypothetical action. All three are real code paths, not
  narrated outcomes.
- This is still a reference orchestration, not a production agent loop:
  there is no live language model call and no live warehouse
  connection. Its value is in proving the control flow and every
  enforcement boundary are real, wired, and in the right order - not in
  being a deployable agent.
- This orchestrator is intentionally framework-free (see the
  framework-agnostic positioning section added to
  `docs/architecture-spec.md`, and the companion mapping documents
  `docs/governance/agent_bricks_mapping.md` and
  `docs/governance/langgraph_mapping.md`), since the point of this file
  is to make the actual enforcement logic and ordering visible in plain
  code, not to demonstrate a framework integration.


## ADR-017: Governance Registry Spreadsheet and Drift Detection

**Status:** Accepted

**Context:**

Every governance and framework-alignment fact in this project so far
lives only in prose (ADR-007's row filters, the HIPAA/ISO/NIST
alignment docs) or only in code (`governance_policies.sql`). Nothing
connects the two, so nothing would catch it if they diverged - if a
row filter were renamed or removed in the SQL, every alignment doc
that references it would go stale silently. Compliance reviewers in
practice also often work from a spreadsheet as their source of truth
rather than reading SQL directly, so a single, structured,
spreadsheet-based registry of access rules and framework mappings is
both a more reviewer-friendly artifact and a checkable one.

**Decision:**

Build `docs/governance/registry/governance_registry.xlsx` as the
single point of reference for this project's access rules, identities,
and HIPAA/ISO 42001/NIST AI RMF mappings, consolidating what was
previously only prose across three separate alignment docs into
structured rows with a Rule ID, table, column, function, and framework
tags. Then build
`observability/governance_registry_check/governance_registry_check.py`
as a lightweight automation that reads that spreadsheet and checks it
against what `governance_policies.sql` actually implements, flagging
drift in both directions: a rule the spreadsheet documents that the
code no longer implements, and a rule the code implements that the
spreadsheet was never updated to reflect.

**Consequences:**

- This was tested against a real, deliberately introduced mismatch
  (renaming a masking function in the SQL without updating the
  spreadsheet) and correctly caught it as two drift findings, then
  correctly reported zero drift once the file was restored - this is
  a genuinely working check, not a placeholder that always passes.
- The parser is intentionally simple, regular-expression matching
  tuned to `governance_policies.sql`'s current, consistent structure,
  not a general-purpose SQL DDL parser. It is accurate against this
  file as it exists today and would need extending if that file's
  structure changed materially - stated plainly rather than
  overclaiming robustness.
- Gap rows (rows explicitly documenting a known, intentional
  limitation rather than a claimed control, such as the row-filter
  join gap already named in ADR-007) are treated as informational and
  are not checked against code, since there is nothing in the code for
  them to match against - only rows claiming an active control are
  checked.
- This does not replace the three narrative alignment docs
  (`HIPAA_alignment.md`, `ISO_42001_alignment.md`,
  `NIST_AI_RMF_alignment.md`); it consolidates their structured facts
  into one checkable artifact and adds drift detection on top,
  consistent with the same enforce-outside-the-model principle used by
  `approval_gate.py` and `sub_agent_delegation.py` - here applied to
  documentation staying honest, not to agent actions.
