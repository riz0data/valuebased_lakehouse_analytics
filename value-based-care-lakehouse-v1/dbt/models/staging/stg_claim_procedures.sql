-- stg_claim_procedures.sql
-- Bridge grain: one row per (claim, procedure) pairing, unpivoted at
-- ingestion time. Feeds lnk_claim_procedure.

select
    claim_line_bk,
    procedure_bk,
    record_source,
    load_dts
from {{ source('bronze', 'synpuf_inpatient_claim_procedures') }}
