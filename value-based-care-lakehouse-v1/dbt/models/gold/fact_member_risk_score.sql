-- fact_member_risk_score.sql
-- Member RAF score fact at member/model-year grain, built from
-- tlnk_member_risk_score_txn. SYNTHETIC RAF values - see
-- ingestion/risk_adjustment/README.md.

select
    t.member_risk_score_txn_hk,
    t.member_hk,
    t.risk_model_hk,
    t.raf_score,
    t.model_year,
    t.effective_from
from {{ ref('tlnk_member_risk_score_txn') }} t
