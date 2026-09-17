# NPPES Ingestion

**Status: Implemented and tested.**

Lands the public NPPES NPI Registry bulk file into the Bronze layer, split
into individual providers (Entity Type 1) and organizations/facilities
(Entity Type 2), with column renaming and de-duplication.

Source: https://download.cms.gov/nppes/NPI_Files.html (public domain, real
provider directory data - contains no patient/member data).

## Files

- `land_nppes.py` - main ingestion script. Supports two engines:
  - `pandas` (default) - runs anywhere, chunked processing for the ~9GB real file
  - `spark` - for running inside an actual Databricks job against Delta
- `nppes_schema.py` - single source of truth for which raw NPPES columns are
  kept and what they're renamed to
- `make_sample.py` - generates a small synthetic sample file in the real
  NPPES column format, used for local testing
- `test_land_nppes.py` - pytest suite covering column selection, provider/
  facility splitting, de-duplication, and error handling
- `sample_nppes.csv` - the sample fixture (fabricated data, correct format)

## Usage

```bash
pip install -r requirements.txt

# Run against a real NPPES bulk file
python land_nppes.py --input /path/to/npidata_pfile_20260101.csv \
    --output-dir ./bronze/nppes

# Run against the included sample for a quick smoke test
python land_nppes.py --input sample_nppes.csv --output-dir ./bronze/nppes --format csv

# Run the test suite
pytest test_land_nppes.py -v
```

## Note on this repo's test data

The real NPPES bulk file is downloaded directly from a CMS server that
isn't reachable from every environment (including the sandbox this repo
was built in). `make_sample.py` generates a small file in the exact
column format of the real thing, with fabricated NPIs and names, so the
ingestion logic can be verified end-to-end without needing that download.
Point `--input` at the real bulk file to use this in production.
