-- fact_appeal.sql
-- Appeal fact at the appeal grain, enriched with the linked claim -
-- feeds Appeal Overturn Rate. SYNTHETIC - see
-- ingestion/payment_integrity/README.md.

select
    a.appeal_hk,
    lca.claim_line_hk,
    a.appeal_status,
    a.appeal_reason
from {{ ref('dim_appeal') }} a
left join {{ ref('lnk_claim_appeal') }} lca
    on a.appeal_hk = lca.appeal_hk
