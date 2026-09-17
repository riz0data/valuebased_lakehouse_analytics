-- fact_claim_payment.sql
-- Claim payment fact at the claim-line grain. Joins the payment
-- transaction (billed/allowed/paid amounts) to the claim's provider and
-- member via lnk_claim_provider_member, and to the claim's DRG via
-- lnk_claim_drg, so this single fact table can answer "leakage by
-- provider", "leakage by DRG", and population-level rollups without
-- further joins - the whole point of the Gold star schema.

select
    t.payment_txn_hk,
    t.claim_line_hk,
    lpm.provider_hk,
    lpm.member_hk,
    ld.drg_hk,
    t.billed_amount,
    t.allowed_amount,
    t.paid_amount,
    (t.billed_amount - t.paid_amount) as leakage_amount,
    t.payment_date,
    cl.service_from_date,
    cl.admission_date
from {{ ref('tlnk_claim_payment_txn') }} t
left join {{ ref('lnk_claim_provider_member') }} lpm
    on t.claim_line_hk = lpm.claim_line_hk
left join {{ ref('lnk_claim_drg') }} ld
    on t.claim_line_hk = ld.claim_line_hk
left join {{ ref('sat_claim_details') }} cl
    on t.claim_line_hk = cl.claim_line_hk
