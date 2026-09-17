# Clinical Quality Ingestion

## Data honesty: what's real, what's synthetic, and what's real-but-existing

Clinical Quality is unusual among this repo's domains: most of its raw
material is **already ingested** - Synthea's `Encounter` and `Condition`
resources (see `ingestion/synthea/`) are real, working ingestion of
genuinely realistic (if synthetic-population) clinical encounter data,
including the provider and facility references added during this domain's
build (see `ingestion/synthea/README.md`). No new ingestion was needed
for encounters themselves.

What's missing, and what this module provides instead:

**Real, not fabricated:**
- The measure codes and names (`BCS-E` Breast Cancer Screening, `CBP`
  Controlling High Blood Pressure, `COL-E` Colorectal Cancer Screening,
  `D09` Medication Adherence for Hypertension, `D10` Medication Adherence
  for Cholesterol) are real CMS Star Ratings measures, published annually
  in the CMS Part C & D Star Ratings Technical Notes (cms.gov). This is a
  representative subset, not the full measure set for any single year.
- The measure weights used here reflect the real Star Ratings concept
  that some measures (like Controlling Blood Pressure) are weighted more
  heavily than others, but the specific weight values are illustrative,
  not copied verbatim from a specific year's technical notes.

**Synthetic (fabricated for this demo):**
- **Which members are evaluated against which measures**, and **every
  member-level evaluation result** (met/not met), is randomly generated.
  CMS Star Ratings are published at the health-plan (contract) level, not
  the member level - whether a specific person got their breast cancer
  screening is exactly the kind of record a real payer holds privately,
  so there's no real data to substitute here, the same situation as
  Risk Adjustment's member-level RAF scores.

## Files

- `make_clinical_quality_sample.py` - deterministic (seeded) generator,
  stdlib only. Produces `measures.csv`, `member_measure.csv`,
  `member_measure_evals.csv`. Takes `--member-bks` (real member business
  keys from the Core domain ingestion).
- `test_make_clinical_quality_sample.py` - 14 tests, all passing.
- `sample_output/` - pre-generated fixture CSVs for 3 sample members.

## Usage

```bash
python3 make_clinical_quality_sample.py \
    --member-bks MBR-001 MBR-002 MBR-003 \
    --output-dir ./sample_output
```

## What feeds the Vault from here vs. from Synthea

- `hub_encounter`, `sat_encounter_details`, `lnk_member_encounter`,
  `lnk_encounter_provider`, `lnk_encounter_facility`, and
  `lnk_encounter_diagnosis` are all built from **real Synthea
  encounter/condition data** - see `ingestion/synthea/`.
- `hub_measure`, `sat_measure_definition`, `lnk_member_measure`, and
  `tlnk_member_measure_eval_txn` are built from **this module's synthetic
  fixtures**.
