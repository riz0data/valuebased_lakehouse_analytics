# Pharmacy Ingestion

## Data honesty: what's real, what's synthetic

**Real, not fabricated:**
- **Drugs** - the FDA National Drug Code (NDC) Directory (`land_ndc.py`)
  is a real, public-domain FDA dataset. It's distributed as two
  tab-delimited files, `product.txt` and `package.txt`, joined on
  `PRODUCTID` - see
  https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
  and the NDC Product/Package File Definitions pages linked from there.
  This repo's `sample_data/product.txt` and `sample_data/package.txt`
  are small hand-built fixtures in the exact real column layout (see
  "Note on sample data" below) - point `--input-dir` at a real
  `ndctext.zip` extraction to use this in production.
- **Pharmacies** - identified from the existing NPPES ingestion
  (`ingestion/nppes/`) by their real NUCC provider taxonomy code,
  `3336C0003X` (Community/Retail Pharmacy), assigned by the National
  Uniform Claim Committee. No new ingestion needed - `hub_pharmacy` is
  built by filtering `stg_providers`/`stg_facilities` on this taxonomy
  code, the same way every other Core-domain Hub already works.

**Synthetic (fabricated for this demo):**
- **Pharmacy fill transactions** - which member filled which drug at
  which pharmacy, and when (`make_pharmacy_fill_sample.py`). There is no
  public dataset of individual prescription fill events - like claims
  and member-level HCC/RAF scores elsewhere in this repo, this is
  protected health information that real payers and PBMs hold privately
  and no open dataset publishes at the individual level.

## Files

- `land_ndc.py` - ingests the real FDA NDC Directory (`product.txt` +
  `package.txt`) into Bronze, preserving FDA's own column names.
- `test_land_ndc.py` - 12 tests, all passing (including orphan-package
  detection when a package references a product not in product.txt).
- `sample_data/` - small fixtures in the exact real NDC Directory format.
- `make_pharmacy_fill_sample.py` - deterministic (seeded) synthetic fill
  transaction generator, stdlib only.
- `test_make_pharmacy_fill_sample.py` - 8 tests, all passing.
- `sample_output/` - pre-generated fixture CSV for 3 sample members.

## Usage

```bash
python3 land_ndc.py --input-dir sample_data --output-dir ./bronze/ndc --format csv

python3 make_pharmacy_fill_sample.py \
    --member-bks MBR-001 MBR-002 MBR-003 \
    --drug-bks 0069-2587 0378-3856 0071-0155 \
    --pharmacy-bks 6789012345 \
    --output-dir ./sample_output
```

## Note on sample data

Real FDA NDC Directory downloads require external network access this
sandbox doesn't have (accessdata.fda.gov isn't on the allowed egress
list). `sample_data/product.txt` and `sample_data/package.txt` are
small hand-built files in the exact real tab-delimited FDA schema - the
real, documented column names, joined the real way (via `PRODUCTID`) -
so the parsing, joining, and orphan-detection logic can be verified
end-to-end without that dependency. Point `--input-dir` at a real
extracted `ndctext.zip` to use this in production.

## What feeds the Vault from here vs. from NPPES

- `hub_drug`, `sat_drug_details` are built from **this module's real NDC
  Directory ingestion** (`land_ndc.py`).
- `hub_pharmacy`, `sat_pharmacy_details` are built from **existing real
  NPPES data**, filtered on taxonomy code `3336C0003X`.
- `lnk_pharmacy_drug`, `lnk_member_pharmacy`, and
  `tlnk_pharmacy_fill_txn` are built from **this module's synthetic fill
  fixtures** (`make_pharmacy_fill_sample.py`).
