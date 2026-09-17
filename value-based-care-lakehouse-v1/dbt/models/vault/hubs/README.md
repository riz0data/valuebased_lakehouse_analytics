# Hub Models

**Status: 16 of 18 Hubs implemented - Core, Payment Integrity, Risk Adjustment, Clinical Quality, and Pharmacy.**

Core: `hub_member`, `hub_provider`, `hub_facility`, `hub_claim_line`, `hub_diagnosis`.

Payment Integrity: `hub_procedure`, `hub_drg`, `hub_contract`,
`hub_authorization`, `hub_appeal` - built using real `automate_dv.hub()`
macro calls against hashed staging models (see `../../staging/*_hk.sql`).
`hub_procedure` and `hub_drg` are sourced from real DE-SynPUF data (with
a documented ICD-9-vs-HCPCS coding-system caveat for procedures);
`hub_contract`, `hub_authorization`, `hub_appeal` are sourced from
clearly-labeled SYNTHETIC fixtures - see
`ingestion/payment_integrity/README.md` for why no open dataset exists
for these entities.

Risk Adjustment: `hub_hcc_category`, `hub_risk_model` - category
codes/descriptions and model versions (V24, V28) are real, CMS-published
facts; see `ingestion/risk_adjustment/README.md`.

Clinical Quality: `hub_encounter`, `hub_measure` - encounters are
real Synthea data; measure codes are real CMS Star Ratings codes - see
`ingestion/clinical_quality/README.md`.

Pharmacy: `hub_drug` (real FDA NDC Directory), `hub_pharmacy` (real
NPPES data, filtered by NUCC taxonomy code `3336C0003X`) - see
`ingestion/pharmacy/README.md`.

Not yet implemented: `hub_plan`, `hub_employer_group` (Core - no
ingestion source yet) - the only 2 of the original 18 Hubs still open,
both blocked on a plan-enrollment data source this repo doesn't ingest.
See `docs/data-vault-model-reference.xlsx` (Hubs sheet).

## Pattern used

Every Hub here follows the same two-step automate_dv pattern:

1. A `stg_<entity>_hk.sql` model in `models/staging/` calls
   `automate_dv.stage()` to compute the hash key from the business key.
2. The Hub model itself calls `automate_dv.hub()` against that hashed
   staging model.

This is the standard AutomateDV pattern (see
https://automate-dv.readthedocs.io) - hash keys are always computed once
in a staging layer and referenced everywhere downstream, never recomputed
inline in a Hub/Link/Satellite.
