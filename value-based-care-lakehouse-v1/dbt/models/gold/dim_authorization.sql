-- dim_authorization.sql
-- Prior authorization dimension, built from hub_authorization +
-- sat_authorization_details. SYNTHETIC - see
-- ingestion/payment_integrity/README.md.

select
    h.authorization_hk,
    h.authorization_bk,
    s.auth_status,
    s.requested_date
from {{ ref('hub_authorization') }} h
left join {{ ref('sat_authorization_details') }} s
    on h.authorization_hk = s.authorization_hk
