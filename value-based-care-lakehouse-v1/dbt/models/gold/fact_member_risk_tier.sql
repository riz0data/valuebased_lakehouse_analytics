-- fact_member_risk_tier.sql
-- Buckets each member/model-year RAF score into a risk tier - feeds
-- Member Risk Tier Distribution. Tier cut points (low under 1.0,
-- medium 1.0 to 2.0, high over 2.0) are an illustrative convention for
-- this repo, not an official CMS threshold - CMS does not publish a
-- standard RAF tiering scheme; payers set their own internally. See
-- ingestion/risk_adjustment/README.md for the underlying SYNTHETIC RAF
-- values.

select
    member_risk_score_txn_hk,
    member_hk,
    risk_model_hk,
    raf_score,
    model_year,
    case
        when raf_score < 1.0 then 'low'
        when raf_score < 2.0 then 'medium'
        else 'high'
    end as risk_tier
from {{ ref('fact_member_risk_score') }}
