-- stg_procedures.sql
-- Procedure codes from DE-SynPUF Inpatient Claims. NOTE: these are
-- ICD-9-CM procedure codes, not HCPCS Level II as originally scoped in
-- the ERD - see ingestion/payment_integrity/README.md for why (DE-SynPUF
-- does not carry HCPCS-level detail in its public release).

select distinct
    procedure_bk,
    'icd9_procedure' as coding_system,
    record_source,
    load_dts
from {{ source('bronze', 'synpuf_inpatient_claim_procedures') }}
