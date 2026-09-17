-- stg_member_risk_scores.sql
-- SYNTHETIC member-level RAF scores. See ingestion/risk_adjustment/README.md.

select
    member_bk,
    risk_model_bk,
    raf_score,
    model_year,
    current_timestamp() as load_dts,
    'ra_member_risk_scores' as record_source
from {{ source('bronze', 'ra_member_risk_scores') }}
