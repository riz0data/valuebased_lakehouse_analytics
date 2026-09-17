-- fact_care_gap.sql
-- Subset of fact_measure_evaluation representing open care gaps (an
-- evaluation with a not-met result) - feeds Care Gap Count. SYNTHETIC
-- eval results - see ingestion/clinical_quality/README.md.

select
    member_measure_eval_txn_hk,
    member_hk,
    measure_hk,
    measure_code,
    eval_result,
    eval_date
from {{ ref('fact_measure_evaluation') }}
where eval_result != 'met'
