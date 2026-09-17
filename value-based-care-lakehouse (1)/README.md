# Value-Based Care Lakehouse
### A Data Vault 2.0 + Databricks Reference Architecture Unifying Payment Integrity, Risk Adjustment, and Clinical Quality

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()
[![Data: 100%25 Open/Synthetic](https://img.shields.io/badge/Data-100%25%20Open%20%2F%20Synthetic-informational)]()
[![Databricks](https://img.shields.io/badge/Databricks-Lakehouse-red)]()
[![dbt](https://img.shields.io/badge/dbt-AutomateDV-orange)]()

---

## The Problem

A health plan or ACO operating under a value-based care contract - Medicare Shared Savings Program, a capitated Medicare Advantage arrangement, a commercial risk contract - is judged on three things happening at once:

1. **Payment Integrity** - are claims paid correctly, without leakage from pricing errors, upcoding, or missed coordination-of-benefits recovery?
2. **Risk Adjustment** - is the plan's risk score (RAF) an accurate reflection of how sick its population actually is, so it's fairly compensated for the risk it carries?
3. **Clinical Quality** - are members actually getting healthier, measured through HEDIS compliance and CMS Star Ratings, which gate whether shared savings get paid out at all?

In most organizations, these three functions run on **separate teams, separate data marts, and separate definitions of the same entities** - "member," "provider," "cost" mean three different things depending on who you ask. The result: nobody can answer the one question that actually determines whether a VBC contract was worth it - *did the savings earned from managing cost and risk outweigh what was spent, net of quality performance?*

This repository is a reference architecture for solving that as a **data modeling problem, not a quarterly reconciliation exercise**: model claims, risk, and quality on a single set of conformed business entities (one `hub_member`, one `hub_provider`, one `hub_diagnosis`), and expose them through one governed semantic layer.

---

## Architecture Overview

**Storage & Compute:** Databricks Lakehouse (Delta Lake, Unity Catalog, Serverless SQL)
**Silver Layer Modeling:** Data Vault 2.0 via the `automate_dv` dbt package (Hubs, Links, Satellites, Transactional Links)
**Gold Layer:** Denormalized star schemas, Liquid Clustered, incrementally materialized
**Semantic Layer:** dbt Semantic Layer - governed metric definitions with row/column-level security
**Data:** 100% open government data and open-source synthetic data - see [`DATA_SOURCES.md`](./DATA_SOURCES.md)

```
Open Data Sources -> Bronze (Auto Loader) -> Silver (Data Vault 2.0) -> Gold (Star Schema) -> Semantic Layer -> BI / Metrics
```

### Entity Relationship Diagram

The full target model - 18 Hubs, 17 Links, 6 Transactional Links, 18 Satellites, spanning Core, Payment Integrity, Risk Adjustment, Clinical Quality, and Pharmacy - is in [`docs/erd.mermaid`](./docs/erd.mermaid) and renders natively on GitHub.

> See the live diagram at [`docs/erd.mermaid`](./docs/erd.mermaid). Build status (implemented vs. modeled-only) is tracked entity-by-entity in [`docs/data-vault-model-reference.xlsx`](./docs/data-vault-model-reference.xlsx).

---

## Key Design Decisions

Full reasoning for each is written up as an Architecture Decision Record in [`docs/decisions/`](./docs/decisions/):

- **[ADR-001](./docs/decisions/001-data-vault-over-flat-model.md)** - Why Data Vault 2.0 over a flat/Kimball-only model for the Silver layer
- **[ADR-002](./docs/decisions/002-transactional-links-for-events.md)** - Why immutable financial and clinical events (payments, adjustments, risk score runs, measure evaluations) are modeled as Transactional Links, not Satellites
- **[ADR-003](./docs/decisions/003-conformed-hubs-across-domains.md)** - Why `hub_member`, `hub_provider`, and `hub_diagnosis` are shared, conformed entities across all three domains instead of domain-siloed copies
- **[ADR-004](./docs/decisions/004-open-data-sourcing.md)** - Why CMS DE-SynPUF and Synthea were chosen over hand-rolled fake data, and why HCPCS was used instead of CPT
- **[ADR-005](./docs/decisions/005-semantic-layer-governance.md)** - Why metric definitions and row/column security live in the dbt Semantic Layer rather than in downstream BI tools

---

## Metrics This Model Is Designed to Support

A sample of the ~30 metrics catalogued in [`docs/data-vault-model-reference.xlsx`](./docs/data-vault-model-reference.xlsx) (Metrics tab), each mapped to its source entities and current build status:

| Metric | Domain | Ties To |
|---|---|---|
| Total Payment Leakage ($) / Leakage Rate (%) | Payment Integrity | `sat_claim_details` |
| DRG Reimbursement Variance | Payment Integrity | `hub_drg`, `lnk_claim_drg` |
| COB/TPL Recovery Amount | Payment Integrity | `tlnk_cob_recovery_txn` |
| RAF Score & YoY Trend | Risk Adjustment | `tlnk_member_risk_score_txn` |
| HCC Capture Rate / Coding Gap Closure Rate | Risk Adjustment | `lnk_diagnosis_hcc_crosswalk`, `sat_member_hcc_status` |
| HEDIS Measure Compliance Rate | Clinical Quality | `tlnk_member_measure_eval_txn` |
| Medication Adherence (PDC) | Clinical Quality | `tlnk_pharmacy_fill_txn` |
| Star Rating Composite Score | Clinical Quality | `sat_measure_definition`, `tlnk_member_measure_eval_txn` |
| **Net VBC Contract Value** | **Cross-Domain** | Shared savings, net of leakage and risk-adjusted cost |
| **Risk-Adjusted Shared Savings Rate** | **Cross-Domain** | Cost performance normalized by RAF |

The last two are the point of the whole exercise: they only exist because Payment Integrity, Risk Adjustment, and Clinical Quality share the same modeled entities.

---

## Who This Is For

**Hiring managers and technical interviewers** - this repo demonstrates production Data Vault 2.0 and Databricks Lakehouse design at the pattern level: entity modeling, incremental processing, Unity Catalog governance, and semantic layer metric design, applied to a real healthcare business problem rather than a toy dataset. The [ADRs](./docs/decisions/) show the *why* behind each structural decision, not just the *what*.

**Startups, nonprofits, and small-to-mid-size healthcare organizations** evaluating how to structure VBC analytics - this is a documented, working pattern you're free to fork and adapt. Be aware of the maturity caveat below before treating it as production-ready.

**Organizations considering advisory support** - if your team is standing up (or struggling with) a Payment Integrity, Risk Adjustment, or Clinical Quality data platform and would benefit from an architect who has built this in production, see [Advisory & Consulting](#advisory--consulting) below.

### Maturity Caveat

This is a **reference architecture and demonstration**, not a deployable product. It runs entirely on open government data and open-source synthetic patient data (see [`DATA_SOURCES.md`](./DATA_SOURCES.md)) - no PHI, no proprietary data, no client-derived artifacts of any kind. Adopting this pattern for real member/patient data requires your own HIPAA-grade controls, data quality hardening, and a Unity Catalog governance model scoped to your environment - none of which is a copy-paste exercise.

---

## Repository Structure

```
value-based-care-lakehouse/
+-- README.md
+-- LICENSE
+-- DATA_SOURCES.md                 # every dataset, its license, and a no-PHI statement
+-- docs/
|   +-- erd.mermaid                 # full entity relationship diagram
|   +-- data-vault-model-reference.xlsx   # entity catalog + metrics tab
|   +-- decisions/                  # architecture decision records (ADRs)
+-- ingestion/                      # DE-SynPUF, Synthea, NPPES landing scripts
+-- dbt/                            # staging, Data Vault, Gold, semantic layer models
+-- databricks.yml                  # Databricks Asset Bundle
+-- .github/workflows/ci.yml        # dbt build + test on every PR
```

---

## Advisory & Consulting

I'm open to **advisory and board-level engagements** with startups, nonprofits, and small-to-mid-size healthcare organizations building or rethinking their Payment Integrity, Risk Adjustment, or Clinical Quality data infrastructure. This repository reflects patterns I've implemented in production for payer-scale claims, risk, and quality data platforms - if your team is early in this journey and wants architectural guidance rather than a from-scratch consulting engagement, reach out.

**Contact:** [your email] . [LinkedIn] . [how you want to be reached]

---

## License

Code in this repository is licensed under [MIT](./LICENSE). All data sources are open government data or open-source synthetic data - see [`DATA_SOURCES.md`](./DATA_SOURCES.md) for the full list and license terms of each.
