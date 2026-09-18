-- stg_appeals.sql
-- SYNTHETIC appeal case fixtures.

select
    appeal_bk,
    claim_line_bk,
    appeal_status,
    appeal_reason,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_appeals') }}
