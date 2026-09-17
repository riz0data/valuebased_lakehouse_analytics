-- stg_risk_models.sql
-- Real CMS-HCC model versions (V24, V28). See ingestion/risk_adjustment/README.md.

select
    risk_model_bk,
    model_name,
    current_timestamp() as load_dts,
    'ra_risk_models' as record_source
from {{ source('bronze', 'ra_risk_models') }}
