# Link Models

**Status: 15 of 17 Links from the original spec implemented, plus 2
additional Links (`lnk_claim_diagnosis`, `lnk_member_suspected_hcc`)
built beyond the spec - see `docs/data-vault-model-reference.xlsx`
(Links sheet) for the official target list.**

Core: `lnk_claim_provider_member`, `lnk_claim_diagnosis`.

Payment Integrity: `lnk_claim_procedure`, `lnk_claim_drg`,
`lnk_provider_contract`, `lnk_claim_authorization`, `lnk_claim_appeal` -
built using real `automate_dv.link()` macro calls. The Contract,
Authorization, and Appeal Links are sourced from SYNTHETIC fixtures - see
`ingestion/payment_integrity/README.md`.

Risk Adjustment: `lnk_member_hcc`, `lnk_diagnosis_hcc_crosswalk` -
member-HCC assignment is SYNTHETIC; the crosswalk is an illustrative
sample, not the full CMS mapping table - see
`ingestion/risk_adjustment/README.md`. Also `lnk_member_suspected_hcc` -
additive beyond the original ERD scope, links a member to an HCC a
suspecting engine flagged as plausible but not yet coded; built
specifically to make HCC Capture Rate and Suspecting Yield Rate
computable, since real diagnosis data in this repo can't be crosswalked
to the ICD-10-CM-only CMS-HCC model (see `../../semantic/README.md` for
the full explanation). SYNTHETIC.

Clinical Quality: `lnk_member_encounter`, `lnk_encounter_provider`,
`lnk_encounter_facility`, `lnk_encounter_diagnosis` (all real Synthea
data - `lnk_encounter_provider`/`lnk_encounter_facility` required adding
the FHIR `participant`/`serviceProvider` field extraction to
`ingestion/synthea/`, see that domain's README), and `lnk_member_measure`
(SYNTHETIC eligibility assignment).

Pharmacy: `lnk_pharmacy_drug`, `lnk_member_pharmacy` - both derived
from the SYNTHETIC pharmacy fill fixtures on real Hubs - see
`ingestion/pharmacy/README.md`.

Not yet implemented: `lnk_member_plan`, `lnk_plan_employer_group` -
both blocked on `hub_plan`/`hub_employer_group` not yet being built
(no plan-enrollment data source ingested - see `../hubs/README.md`).

## Note on lnk_claim_diagnosis and lnk_claim_procedure

Both are direct pass-throughs of unpivots already done at the ingestion
layer (`ingestion/de_synpuf/land_de_synpuf.py` flattens the raw file's
wide `ICD9_DGNS_CD_1..10` and `ICD9_PRCDR_CD_1..6` columns into tidy rows
before either Link ever sees the data) - the unpivot logic lives in
ingestion, not in dbt, so it only has to be written and tested once.
