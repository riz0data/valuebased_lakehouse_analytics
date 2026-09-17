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
