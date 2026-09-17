# Satellite Models

**Status: 15 of 19 Satellites implemented - Core, Payment Integrity, Risk Adjustment, Clinical Quality, and Pharmacy.**

Core: `sat_member_demographics`, `sat_provider_details`, `sat_claim_details`.

Payment Integrity: `sat_procedure_details`, `sat_drg_details`,
`sat_contract_details`, `sat_authorization_details`, `sat_appeal_details`
- built using real `automate_dv.sat()` macro calls with hashdiff-based
change tracking. `sat_procedure_details` carries a minimal payload since DE-SynPUF only
provides bare procedure codes, not descriptions - see
`ingestion/payment_integrity/README.md`. `sat_drg_details` was
extended to join a real (illustrative-subset) CMS MS-DRG relative
weight reference table on top of the bare DE-SynPUF DRG code, so it now
carries a real description and weight for the DRG codes that table
covers (291, 292, 293, 470) - this is what makes DRG Reimbursement
Variance computable. The Contract, Authorization, and
Appeal satellites are sourced from SYNTHETIC fixtures.

Risk Adjustment: `sat_hcc_category_details`, `sat_risk_model_details`,
`sat_member_hcc_status` - category details use real codes/descriptions
with illustrative weights. `sat_member_hcc_status` now tracks a real
coding-gap lifecycle (`active_flag`, `coding_gap_identified_date`,
`coding_gap_closed_date`) - the synthetic generator was extended to
emit these fields, replacing the earlier hardcoded "always active, no
gap" placeholder, which is what makes Coding Gap Closure Rate
computable - see `ingestion/risk_adjustment/README.md`.

Clinical Quality: `sat_encounter_details` (real Synthea data, now
also carrying `encounter_end` for Readmission Rate),
`sat_measure_definition` (real CMS measure names; illustrative weights).

Pharmacy: `sat_drug_details` (real FDA NDC Directory data),
`sat_pharmacy_details` (real NPPES data).

Not yet implemented: the remaining 4 Satellites - see
`docs/data-vault-model-reference.xlsx` (Satellites sheet); these are
spread across Core (`hub_facility`/`hub_diagnosis` currently have no
Satellite, e.g. no descriptive attributes ingested beyond the Hub's own
business key) rather than blocked on any remaining domain.

## Pattern used

Each Satellite's hashing layer (`stg_<entity>_sat_hk.sql` in
`models/staging/`) computes both the parent hash key AND a `hashdiff` -
a hash over just the descriptive/payload columns - via automate_dv's
`is_hashdiff: true` stage() configuration. This is what lets `sat()`
detect when a record's attributes have actually changed between loads
versus when it's an unchanged re-load.
