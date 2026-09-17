-- fact_authorization.sql
-- Prior authorization fact at the authorization grain, enriched with
-- the linked claim - feeds Prior Authorization Approval Rate.
-- SYNTHETIC - see ingestion/payment_integrity/README.md.

select
    a.authorization_hk,
    lca.claim_line_hk,
    a.auth_status,
    a.requested_date
from {{ ref('dim_authorization') }} a
left join {{ ref('lnk_claim_authorization') }} lca
    on a.authorization_hk = lca.authorization_hk
