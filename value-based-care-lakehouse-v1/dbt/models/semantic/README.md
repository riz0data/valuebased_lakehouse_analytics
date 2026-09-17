# Semantic Layer

**Status: 24 of ~30 metrics implemented - every Payment Integrity, Risk
Adjustment, and Clinical Quality metric in the spec is now "Ready
Today," plus Medication Adherence (PDC) from Pharmacy.**

This folder is the dbt Semantic Layer (MetricFlow) definitions: the layer
that turns Gold star-schema tables into governed, reusable business
metrics that any BI tool or the Semantic Layer API can query with a
single consistent definition, rather than every analyst writing their
own slightly-different SQL for "leakage."

## The full lineage this repo demonstrates, end to end

Bronze (raw ingestion output, see `/ingestion`) feeds Staging (typed,
renamed, unioned across sources, see `/dbt/models/staging`) feeds the
Data Vault - Hubs, Links, Satellites, Transactional Links (see
`/dbt/models/vault`) feeds Gold (star schema, see `/dbt/models/gold`)
feeds this Semantic Layer, which is what a business stakeholder or
hiring manager should actually look at to see the payoff of all the
layers underneath.

## Files

- `_semantic_models.yml` - declares 17 semantic models, each wrapping
  one Gold fact table, with their entities (join keys), dimensions
  (things to group/slice by), and measures (raw aggregatable numbers -
  sums, counts, averages)
- `_metrics.yml` - the 24 business-facing metrics built on those
  measures (plus 2 small intermediate simple metrics - `ed_encounters`,
  `distinct_members` - that only exist to feed the `ed_utilization_rate`
  derived metric)

## Metrics implemented, by domain

### Payment Integrity (10 of 10 - all implemented)

- **Total Payment Leakage** - `simple`: billed minus paid, summed.
- **Payment Leakage Rate** - `ratio`: total leakage over total billed amount.
- **Leakage by Provider** - the same leakage measure under its own
  metric name; query with `--group-by provider`.
- **DRG Reimbursement Variance** - `simple`: sum of (actual paid minus
  expected paid) across DRG-coded claims. Real DE-SynPUF claims and real
  CMS MS-DRG relative weights (a small illustrative subset - DRGs
  291/292/293/470 - verified via web search, not pulled from a live CMS
  file); "expected" payment is a population dollars-per-weight-unit
  benchmark computed from this dataset's own claims, not a true CMS IPPS
  payment calculation (which needs a hospital's wage index and other
  facility-specific inputs this repo doesn't have) - see
  `fact_drg_reimbursement_variance.sql` and
  `ingestion/payment_integrity/README.md`.
- **Denial Rate** - `ratio`: adjustment transactions reason-coded as
  denials (`CO-*` codes) over all adjustment transactions.
- **Days to Adjudication** - `simple`: average days between service date
  and payment date.
- **COB / TPL Recovery Amount** - `simple`: sum of COB recovery amounts.
  SYNTHETIC - see `ingestion/payment_integrity/README.md`.
- **Prior Authorization Approval Rate** - `ratio`: approved
  authorizations over all authorizations. SYNTHETIC.
- **Appeal Overturn Rate** - `ratio`: overturned appeals over all
  appeals. SYNTHETIC.
- **YoY Leakage Trend** - `derived`: Total Payment Leakage offset by one
  year, subtracted, for "this year vs. last year" queried directly.

### Risk Adjustment (7 of 7 - all implemented)

- **RAF Score** - `simple`: average member-level CMS-HCC RAF score.
  SYNTHETIC RAF values - see `ingestion/risk_adjustment/README.md`.
- **YoY RAF Score Trend** - `derived`: RAF Score offset by one year, subtracted.
- **HCC Capture Rate** - `ratio`: HCCs both suspected and captured, over
  all suspected HCCs. Built from a new SYNTHETIC "suspected HCC" fixture
  deliberately separate from the existing "captured/coded HCC" fixture -
  see below for why this couldn't be derived from this repo's real
  diagnosis data.
- **Suspecting Yield Rate** - the same suspected/captured comparison as
  HCC Capture Rate, exposed under its own metric name to match how a
  Risk Adjustment stakeholder asks for it.
- **Coding Gap Closure Rate** - `ratio`: closed coding gaps over
  identified coding gaps. The synthetic generator now emits a full gap
  lifecycle (`active_flag`, `coding_gap_identified_date`,
  `coding_gap_closed_date`) - previously every assignment was hardcoded
  "active" with no gap tracking at all.
- **Risk Score Accuracy** - `ratio`: actual (coded) RAF over a
  simplified "clinically suspected" RAF approximation (sum of suspected
  HCCs' weights). A real CMS-HCC RAF score also includes demographic
  factors and disease-hierarchy interaction terms this simplification
  doesn't model - see `fact_risk_score_accuracy.sql`.
- **Member Risk Tier Distribution** - `simple`: member count, queried
  with `--group-by risk_tier` (low/medium/high buckets on RAF score -
  an illustrative repo convention, not a CMS standard).

**On "suspected HCC" being a new synthetic fixture, not derived from
diagnosis data:** the real CMS-HCC diagnosis-to-HCC crosswalk is
ICD-10-CM only (HCC risk adjustment has used ICD-10-CM exclusively since
2015), but this repo's real diagnosis data is ICD-9-CM (DE-SynPUF) or
SNOMED CT (Synthea) - see ADR-004 in `docs/decisions/ADRs.md`, which
already declines to cross-walk SNOMED to ICD for the same reason.
Cross-walking either coding system to ICD-10-CM was judged out of scope
for a portfolio project, so "suspected HCC" is a clearly-labeled
synthetic fixture (`make_suspected_hcc` in
`ingestion/risk_adjustment/make_risk_adjustment_sample.py`) rather than
a suspecting-engine result derived from real diagnosis codes.

### Clinical Quality (7 of 7 - all implemented)

- **HEDIS-style Measure Compliance Rate** - `ratio`: measures met over
  all evaluations. SYNTHETIC eval results - see
  `ingestion/clinical_quality/README.md`.
- **Star Rating Composite Score** - `ratio`: measure weight for measures
  met, over total possible weight. Real CMS Star Ratings weighting
  concept, illustrative weight values.
- **ED Utilization Rate** - `derived`: emergency-classed encounters per
  distinct member, times 1000. Real Synthea encounter data.
- **Preventive Screening Completion Rate** - `ratio`: completed over
  eligible evaluations, filtered to the two real CMS Star Ratings
  measure codes that are actual preventive screenings (`BCS-E` Breast
  Cancer Screening, `COL-E` Colorectal Cancer Screening). SYNTHETIC eval
  results on real measure codes.
- **Care Gap Count** - `simple`: count of open care gaps (not-met
  evaluations), queried with `--group-by member`. SYNTHETIC.
- **Readmission Rate** - `ratio`: index inpatient encounters followed by
  another inpatient encounter for the same member within 30 days, over
  all index inpatient encounters. Real Synthea encounter data - `IMP`
  (inpatient) is a real FHIR R4 `Encounter.class` code. 2 inpatient
  encounter fixtures (an admission and a 14-day readmission) were added
  to `ingestion/synthea/sample_bundles/patient-001.json` specifically to
  demonstrate this, since the original sample data had no inpatient
  encounters at all. General all-cause version - no planned-readmission
  exclusions or condition-specific cohort logic, unlike the real CMS
  measure - see `fact_readmission.sql`.

### Pharmacy (1 of 4)

- **Medication Adherence (PDC)** - `ratio`: total days covered over
  total possible days in a fixed observation period. SYNTHETIC fill
  events; the PDC calculation itself is a simplified days-supply-sum
  approximation, not a full date-overlap calculation - see
  `fact_medication_adherence.sql` and `ingestion/pharmacy/README.md`.

## Why 24, not ~30

The remaining 6 metrics (Medication Possession Ratio, Generic Dispensing
Rate, Polypharmacy Rate in Pharmacy; Net VBC Contract Value,
Risk-Adjusted Shared Savings Rate, Quality Gate Achievement in
Cross-Domain) were out of scope for this build pass, which focused on
Payment Integrity, Risk Adjustment, and Clinical Quality only. Medical
Loss Ratio is explicitly marked "Data Gap" rather than "Requires
Build-Out" in `docs/data-vault-model-reference.xlsx` (Metrics sheet),
since no source in this repo's data-honesty scope (real or
synthesizable) covers premium revenue - see that sheet's "Build Status"
column for the honest status of every metric.

## How to actually run this

```bash
dbt deps
dbt build
dbt sl query --metrics total_payment_leakage,payment_leakage_rate --group-by metric_time
dbt sl query --metrics leakage_by_provider --group-by provider
dbt sl query --metrics drg_reimbursement_variance --group-by metric_time
dbt sl query --metrics cob_tpl_recovery_amount --group-by metric_time
dbt sl query --metrics prior_authorization_approval_rate,appeal_overturn_rate --group-by metric_time
dbt sl query --metrics raf_score,yoy_raf_score_trend --group-by metric_time
dbt sl query --metrics hcc_capture_rate,suspecting_yield_rate,coding_gap_closure_rate --group-by metric_time
dbt sl query --metrics risk_score_accuracy --group-by metric_time
dbt sl query --metrics member_risk_tier_distribution --group-by risk_tier
dbt sl query --metrics hedis_style_measure_compliance_rate,star_rating_composite_score --group-by measure_code
dbt sl query --metrics ed_utilization_rate --group-by metric_time
dbt sl query --metrics preventive_screening_completion_rate --group-by measure_code
dbt sl query --metrics care_gap_count --group-by member
dbt sl query --metrics readmission_rate --group-by metric_time
dbt sl query --metrics medication_adherence_pdc --group-by metric_time
```

(Requires a real dbt Semantic Layer connection - not runnable in this
sandbox, same network/install constraints noted throughout `/ingestion`
and `/dbt` READMEs. The YAML here has been validated to parse correctly
against the MetricFlow v2 spec.)
