-- fact_claim_adjustment.sql
-- Claim adjustment fact: one row per adjustment event (write-off, denial
-- reason, etc.), used to compute Denial Rate.

select
    t.adjustment_txn_hk,
    t.claim_line_hk,
    lpm.provider_hk,
    lpm.member_hk,
    t.adjustment_amount,
    t.adjustment_reason_code,
    t.adjustment_date
from {{ ref('tlnk_claim_adjustment_txn') }} t
left join {{ ref('lnk_claim_provider_member') }} lpm
    on t.claim_line_hk = lpm.claim_line_hk
