-- fact_preventive_screening.sql
-- Subset of fact_measure_evaluation filtered to the real CMS Star
-- Ratings measures that are preventive screenings (BCS-E Breast Cancer
-- Screening, COL-E Colorectal Cancer Screening) - feeds Preventive
-- Screening Completion Rate. SYNTHETIC eval results on real measure
-- codes - see ingestion/clinical_quality/README.md.

select
    member_measure_eval_txn_hk,
    member_hk,
    measure_hk,
    measure_code,
    eval_result,
    eval_date,
    case when eval_result = 'met' then 1 else 0 end as is_completed
from {{ ref('fact_measure_evaluation') }}
where measure_code in ('BCS-E', 'COL-E')
