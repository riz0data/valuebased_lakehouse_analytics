-- fact_cob_recovery.sql
-- Coordination-of-Benefits recovery fact: one row per recovery event,
-- used to compute COB / TPL Recovery Amount.

select
    t.cob_recovery_txn_hk,
    t.claim_line_hk,
    lpm.member_hk,
    t.recovery_amount,
    t.recovery_date
from {{ ref('tlnk_cob_recovery_txn') }} t
left join {{ ref('lnk_claim_provider_member') }} lpm
    on t.claim_line_hk = lpm.claim_line_hk
