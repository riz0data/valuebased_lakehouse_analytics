-- stg_claim_diagnoses.sql
-- Bridge grain: one row per (claim, diagnosis) pairing, already unpivoted
-- at ingestion time in ingestion/de_synpuf/land_de_synpuf.py. This feeds
-- lnk_claim_diagnosis directly.

select
    claim_line_bk,
    diagnosis_bk,
    record_source,
    load_dts
from {{ source('bronze', 'synpuf_inpatient_claim_diagnoses') }}
