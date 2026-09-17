-- stg_diagnosis_hcc_crosswalk.sql
-- Illustrative sample of the diagnosis-to-HCC crosswalk, NOT the full
-- CMS-published mapping table. See ingestion/risk_adjustment/README.md.

select
    diagnosis_bk,
    hcc_bk,
    risk_model_bk,
    current_timestamp() as load_dts,
    'ra_diagnosis_hcc_crosswalk' as record_source
from {{ source('bronze', 'ra_diagnosis_hcc_crosswalk') }}
