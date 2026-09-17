-- dim_appeal.sql
-- Appeal case dimension, built from hub_appeal + sat_appeal_details.
-- SYNTHETIC - see ingestion/payment_integrity/README.md.

select
    h.appeal_hk,
    h.appeal_bk,
    s.appeal_status,
    s.appeal_reason
from {{ ref('hub_appeal') }} h
left join {{ ref('sat_appeal_details') }} s
    on h.appeal_hk = s.appeal_hk
