-- fact_measure_evaluation.sql
-- Quality measure evaluation fact, built from
-- tlnk_member_measure_eval_txn, enriched with the measure's weight for
-- Star Rating Composite Score. SYNTHETIC eval results - see
-- ingestion/clinical_quality/README.md.

select
    t.member_measure_eval_txn_hk,
    t.member_hk,
    t.measure_hk,
    dm.measure_code,
    dm.measure_weight,
    t.eval_result,
    t.eval_date,
    t.effective_from
from {{ ref('tlnk_member_measure_eval_txn') }} t
left join {{ ref('dim_measure') }} dm
    on t.measure_hk = dm.measure_hk
