-- stg_member_measure_evals.sql
-- SYNTHETIC member-level measure evaluation results. See
-- ingestion/clinical_quality/README.md.

select
    member_bk,
    measure_bk,
    eval_result,
    cast(eval_date as date) as eval_date,
    current_timestamp() as load_dts,
    'cq_member_measure_evals' as record_source
from {{ source('bronze', 'cq_member_measure_evals') }}
