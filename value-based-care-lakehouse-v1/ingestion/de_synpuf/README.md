# DE-SynPUF Ingestion

**Status: Implemented and tested.**

Lands two CMS DE-SynPUF file types into the Bronze layer:

- **Beneficiary Summary File** - one row per synthetic beneficiary per year:
  demographics, chronic condition flags, annual cost summaries.
- **Inpatient Claims File** - split into three normalized outputs:
  - claim header (one row per claim)
  - claim diagnoses (unpivoted from the raw file's 10 wide `ICD9_DGNS_CD_1..10` columns)
  - claim procedures (unpivoted from the raw file's 6 wide `ICD9_PRCDR_CD_1..6` columns)

The diagnosis/procedure unpivot is the main real-world wrinkle in this file
format: CMS ships DE-SynPUF with codes spread across fixed wide columns
rather than as normalized rows, and any usable ingestion has to flatten
that before it can feed `hub_diagnosis` / `lnk_claim_diagnosis` in the Vault.

Source: https://www.cms.gov/data-research/statistics-trends-reports/medicare-claims-synthetic-public-use-files
(CMS synthetic public use data, ICD-9-CM codes, both public/free to use.)

## Files

- `land_de_synpuf.py` - main ingestion script (Beneficiary Summary + Inpatient Claims)
- `de_synpuf_schema.py` - column maps and the wide-column lists that get unpivoted
- `make_sample.py` - generates small sample files in the real DE-SynPUF column format
- `test_land_de_synpuf.py` - pytest suite covering renaming, de-dup, the
  diagnosis/procedure unpivot, and error handling
- `sample_bene_summary.csv`, `sample_inpatient_claims.csv` - fixtures (fabricated data, correct format)

## Usage

```bash
pip install -r requirements.txt

python land_de_synpuf.py \
    --bene-input DE1_0_2010_Beneficiary_Summary.csv \
    --inpatient-input DE1_0_2010_Inpatient_Claims.csv \
    --output-dir ./bronze/de_synpuf

# Quick smoke test against the included samples
python land_de_synpuf.py \
    --bene-input sample_bene_summary.csv \
    --inpatient-input sample_inpatient_claims.csv \
    --output-dir ./bronze/de_synpuf --format csv

pytest test_land_de_synpuf.py -v
```

## Note on this repo's test data

The real DE-SynPUF files are downloaded from a CMS server that isn't
reachable from every environment (including the sandbox this repo was
built in). `make_sample.py` generates small files in the exact column
format of the real thing, with fabricated IDs, so the ingestion logic -
including the diagnosis/procedure unpivot - can be verified end-to-end
without that download. Point `--bene-input` / `--inpatient-input` at the
real files to use this in production.

## Not yet covered

Outpatient Claims, Carrier Claims, and Prescription Drug Events file
types follow the same wide-column pattern but aren't implemented yet.
