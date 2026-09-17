# Payment Integrity Ingestion

**Status: Partially real, partially synthetic-by-necessity - read carefully.**

Payment Integrity in this repo's Vault model needs five business entities:
Procedure, DRG, Contract, Prior Authorization, and Appeal, plus three
transactional facts: Payment, Adjustment, and COB Recovery transactions.
Unlike NPPES, DE-SynPUF, and Synthea, **there is no open public dataset
for managed-care contract terms, prior-authorization workflow, appeals,
or claim-level payment/adjustment transaction detail** - this is
proprietary payer operational data in the real world, and no CMS or
MITRE public-use file covers it.

## What's real

- **DRG**: `CLM_DRG_CD` is a genuine field already captured in
  `ingestion/de_synpuf/land_de_synpuf.py`'s Inpatient Claims header output
  - no new ingestion needed, `hub_drg` sources directly from real
  DE-SynPUF data.
- **Procedure**: DE-SynPUF's Inpatient Claims file has 6 wide procedure
  code columns (`ICD9_PRCDR_CD_1..6`), already unpivoted into
  `inpatient_claim_procedures` by the existing ingestion. **Important
  caveat**: these are ICD-9-CM procedure codes, not HCPCS Level II codes
  as originally scoped in the ERD - DE-SynPUF predates HCPCS-level
  granularity in its public release. `hub_procedure` in this repo is
  therefore keyed on the real ICD-9 procedure codes DE-SynPUF actually
  provides, with the coding-system substitution documented here rather
  than silently glossed over.

## What's fabricated

`make_payment_integrity_sample.py` generates small, clearly-synthetic
fixture files for Contract, Provider-Contract attachment, Prior
Authorization, Appeal, and the three transaction types. This is
fabricated data for demonstration purposes only - it is not derived from
CMS, Synthea, or NPPES, and should not be mistaken for realistic claims
payment behavior. It exists so the Payment Integrity Vault models have
something to build and test against end-to-end.

## Files

- `make_payment_integrity_sample.py` - deterministic (seeded) synthetic
  fixture generator
- `test_make_payment_integrity_sample.py` - pytest suite (8 tests)
- `sample_output/` - pre-generated fixtures from a sample run, ready to
  point the dbt sources at directly

## Usage

```bash
python make_payment_integrity_sample.py \
    --claim-bks CLM-001 CLM-002 CLM-003 CLM-004 \
    --provider-bks NPI-1111111111 NPI-2222222222 \
    --output-dir ./sample_output

pytest test_make_payment_integrity_sample.py -v
```

In a real deployment, replace this generator with an actual extract from
your claims/payer-operations system - the field shapes here
(`contract_bk`, `authorization_bk`, `appeal_bk`, transaction amounts and
dates) mirror what a real payer's contract management and claims
adjudication systems would export.


## DRG relative weights (added for DRG Reimbursement Variance)

`reference_data/drg_weights.csv` is a small, real reference table of CMS
MS-DRG relative weights, covering just the DRG codes DE-SynPUF's sample
Inpatient Claims file actually contains (291, 292) plus two more common
DRGs for demonstration breadth (293, 470). Values were verified via web
search against published MS-DRG weight references rather than pulled
directly from a CMS IPPS ZIP file (this sandbox has no network access to
`cms.gov`) - source-year snapshots differ slightly across publishers, so
treat these as illustrative rather than a single official CMS vintage.
This is a static reference table, not something with its own ingestion
script - land it at `bronze.drg_weights` the same way any other small
reference CSV would be loaded, and `stg_drgs.sql` joins to it on
`drg_bk`.

In a real deployment, replace this with the actual CMS IPPS MS-DRG
weight file for your fiscal year:
https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps/acute-inpatient-files-download
