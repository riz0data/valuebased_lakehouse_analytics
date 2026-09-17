# Gold Layer

**Status: 12 of 15 Gold tables from the original spec implemented, plus
16 additional supporting tables built to enable specific metrics that
weren't in the original 15-table list - see
`docs/data-vault-model-reference.xlsx` (Gold Mapping sheet) for the
official target list.**

This is the star schema layer built on top of the Data Vault - plain dbt
SQL models (no automate_dv macros here; Vault mechanics are done by this
point), shaped for direct BI-tool consumption and as the source for the
Semantic Layer (`../semantic/`).

Implemented, from the original 15-table spec:
- `dim_member` - from `hub_member` + `sat_member_demographics`
- `dim_provider` - from `hub_provider` + `sat_provider_details`
- `dim_procedure` - from `hub_procedure` + `sat_procedure_details`
- `dim_hcc_category` - from `hub_hcc_category` + `sat_hcc_category_details`
- `dim_measure` - from `hub_measure` + `sat_measure_definition`
- `dim_drug` - from `hub_drug` + `sat_drug_details` (real FDA NDC Directory data)
- `fact_claim_payment` - from `tlnk_claim_payment_txn`, enriched with
  provider/member/DRG keys via `lnk_claim_provider_member` and
  `lnk_claim_drg`, and claim dates via `sat_claim_details`
- `fact_claim_adjustment` - from `tlnk_claim_adjustment_txn`
- `fact_cob_recovery` - from `tlnk_cob_recovery_txn`
- `fact_member_risk_score` - from `tlnk_member_risk_score_txn`
- `fact_measure_evaluation` - from `tlnk_member_measure_eval_txn`, enriched with measure weight
- `fact_pharmacy_fill` - from `tlnk_pharmacy_fill_txn`, enriched with the drug's NDC

Additional tables built beyond the original spec, to support specific
metrics that needed a Gold-layer home the 15-table list didn't provide:

Clinical Quality / Pharmacy (built in an earlier pass):
- `dim_encounter` - from `hub_encounter` + `sat_encounter_details` (real Synthea data)
- `fact_encounter` - from `hub_encounter`, enriched with member/provider/facility keys - feeds ED Utilization Rate and Readmission Rate
- `fact_medication_adherence` - per-member, per-drug simplified PDC
  calculation over `fact_pharmacy_fill` - feeds Medication Adherence
  (PDC); see the model's own header comment on the day-count
  approximation it makes

Payment Integrity metrics build-out:
- `dim_drg` - from `hub_drg` + `sat_drg_details`, now enriched with real
  (illustrative-subset) CMS MS-DRG relative weights - feeds DRG
  Reimbursement Variance
- `fact_drg_reimbursement_variance` - per-claim actual-vs-expected
  reimbursement comparison; "expected" is a population dollars-per-
  weight-unit benchmark, not a true CMS IPPS payment calculation - see
  the model's own header comment
- `dim_authorization`, `fact_authorization` - prior authorization
  dimension/fact - feeds Prior Authorization Approval Rate. SYNTHETIC.
- `dim_appeal`, `fact_appeal` - appeal case dimension/fact - feeds Appeal
  Overturn Rate. SYNTHETIC.

Risk Adjustment metrics build-out:
- `fact_hcc_capture` - per-member, per-HCC suspected-vs-captured
  comparison - feeds HCC Capture Rate and Suspecting Yield Rate.
  SYNTHETIC (see `../semantic/README.md` for why "suspected HCC" is a
  new fixture rather than derived from real diagnosis data).
- `fact_coding_gap` - per-member-HCC coding-gap lifecycle - feeds Coding
  Gap Closure Rate. SYNTHETIC, now with a real gap-lifecycle generator
  (previously every assignment was hardcoded "active").
- `fact_member_risk_tier` - RAF score bucketed into low/medium/high -
  feeds Member Risk Tier Distribution. SYNTHETIC.
- `fact_risk_score_accuracy` - actual RAF vs. a simplified suspected-RAF
  approximation - feeds Risk Score Accuracy. SYNTHETIC; see the model's
  own header comment on the HCC-weight-sum simplification.

Clinical Quality metrics build-out:
- `fact_readmission` - 30-day all-cause readmission fact from real
  Synthea inpatient encounters - feeds Readmission Rate. General
  all-cause version, no planned-readmission exclusions - see the
  model's own header comment.
- `fact_preventive_screening` - preventive-screening subset of
  `fact_measure_evaluation` (BCS-E, COL-E) - feeds Preventive Screening
  Completion Rate. SYNTHETIC eval results on real measure codes.
- `fact_care_gap` - open-care-gap subset of `fact_measure_evaluation` -
  feeds Care Gap Count. SYNTHETIC.

Together, this is deliberately the exact slice needed to support the
24 "Ready Today" metrics in `docs/data-vault-model-reference.xlsx`
(Metrics sheet) for the domains currently built - see
`../semantic/README.md` for how these Gold tables feed those metrics
directly.

Not yet implemented from the original spec: `dim_facility`,
`dim_diagnosis`, `dim_plan` - all blocked on a plan-enrollment data
source this repo doesn't ingest (`dim_plan`) or on standalone
Satellites for those Hubs not yet built (`dim_facility`,
`dim_diagnosis`). See `docs/data-vault-model-reference.xlsx` (Gold
Mapping sheet) for the full 15-table target and each one's Vault
source.
