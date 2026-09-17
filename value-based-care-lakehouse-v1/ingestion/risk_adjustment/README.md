# Risk Adjustment Ingestion

## Data honesty: what's real, what's synthetic

Unlike Payment Integrity, Risk Adjustment sits closer to public data - CMS
does publish real, authoritative reference materials for the CMS-HCC
model (model versions, the diagnosis-to-HCC crosswalk file, relative
factor tables). This module uses those real facts where they're usable
in a demo repo, and is explicit about what's still synthetic:

**Real, not fabricated:**
- CMS-HCC model versions **V24** and **V28** are real, CMS-published
  risk adjustment model versions. V28 is the current model, phased in
  starting payment year 2024, replacing V24.
- The **HCC category numbers and descriptions** used here (e.g. HCC8
  "Metastatic Cancer and Acute Leukemia", HCC18 "Diabetes with Chronic
  Complications") are real CMS-HCC V28 category numbers, not invented
  ones - see `make_risk_adjustment_sample.py` for the full list and
  source citation. This is a representative **subset** of the real
  ~115-category V28 model, not the complete list.

**Synthetic (fabricated for this demo):**
- The full diagnosis-to-HCC crosswalk is a large, CMS-published lookup
  table (thousands of ICD-10-CM codes mapped to ~115 HCCs). This module
  ships only a small illustrative sample of that mapping (6 codes), not
  the authoritative CMS crosswalk file.
- **Which HCCs each member is assigned**, and every **member-level RAF
  score**, is randomly generated. CMS does not publish member-level risk
  scores - a member's risk score is derived from their own private
  diagnosis history, so there is no "real" data to substitute here.
  These numbers exist purely to demonstrate the Vault → Gold → Semantic
  Layer pipeline mechanics, not to represent any real population's risk
  profile.

## Files

- `make_risk_adjustment_sample.py` - deterministic (seeded) generator,
  stdlib only. Produces `risk_models.csv`, `hcc_categories.csv`,
  `diagnosis_hcc_crosswalk.csv`, `member_hcc.csv`,
  `member_risk_scores.csv`, and `suspected_hcc.csv`. Takes `--member-bks` (member business keys
  to attach synthetic HCC/RAF data to - use real member IDs from the
  Core domain ingestion) and `--diagnosis-bks` (diagnosis codes to
  attempt to crosswalk - defaults to the 6 illustrative sample codes).
- `test_make_risk_adjustment_sample.py` - 28 tests, all passing (run via
  `python3 test_make_risk_adjustment_sample.py`). This is a manual
  assertion script, not `def test_*` pytest functions - written this way
  because pytest is not installable in the sandbox this was built in
  (see repo-root environment notes). In real CI this runs as a plain
  script (`python test_make_risk_adjustment_sample.py`), not via pytest -
  see `.github/workflows/ci.yml`.
- `sample_output/` - pre-generated fixture CSVs for 3 sample members.

## Usage

```bash
python3 make_risk_adjustment_sample.py \
    --member-bks MBR-001 MBR-002 MBR-003 \
    --output-dir ./sample_output
```

## Real reference material for building this out further

If replacing the synthetic diagnosis-HCC crosswalk with the real CMS
file, see CMS's published V28 model documentation and the official
diagnosis-to-HCC crosswalk release (updated annually with the Rate
Announcement) at cms.gov - not included here since it's a large
reference file better downloaded fresh than vendored into a portfolio
repo.

## Extended for the Risk Adjustment metrics build-out

Two additions were made to `make_risk_adjustment_sample.py` specifically
to make HCC Capture Rate, Suspecting Yield Rate, Risk Score Accuracy,
and Coding Gap Closure Rate computable (all previously "Requires
Build-Out"):

- **Coding-gap lifecycle on `member_hcc.csv`**: previously every
  member-HCC assignment was implicitly "active" with no gap tracking at
  all. `make_member_hcc` now also emits `active_flag`,
  `coding_gap_identified_date`, and `coding_gap_closed_date` per
  assignment (about 60% of gaps get a closed date; the rest remain
  open), which flows through `sat_member_hcc_status` to
  `fact_coding_gap` and Coding Gap Closure Rate.
- **New `suspected_hcc.csv` fixture** (`make_suspected_hcc`): a
  SYNTHETIC "what a suspecting engine would flag" HCC assignment per
  member, deliberately generated from a different random seed than
  `member_hcc.csv`'s "captured/coded" assignments so the two can
  meaningfully differ. This could not be derived from this repo's real
  diagnosis data - the real CMS-HCC diagnosis-to-HCC crosswalk is
  ICD-10-CM only, but this repo's real diagnosis codes are ICD-9-CM
  (DE-SynPUF) or SNOMED CT (Synthea) - see ADR-004 in
  `docs/decisions/ADRs.md`, which already declines a SNOMED-to-ICD
  crosswalk for the same out-of-scope reasoning. Feeds
  `lnk_member_suspected_hcc` and `fact_hcc_capture`.
