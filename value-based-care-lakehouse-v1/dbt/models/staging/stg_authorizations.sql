-- stg_authorizations.sql
-- SYNTHETIC prior authorization fixtures.

select
    authorization_bk,
    claim_line_bk,
    auth_status,
    cast(requested_date as date) as requested_date,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_authorizations') }}
