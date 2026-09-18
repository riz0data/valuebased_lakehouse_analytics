-- stg_adjustment_txns.sql
-- SYNTHETIC claim adjustment transaction fixtures.

select
    txn_bk,
    claim_line_bk,
    cast(adjustment_amount as decimal(12,2)) as adjustment_amount,
    adjustment_reason_code,
    cast(adjustment_date as date) as adjustment_date,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_adjustment_transactions') }}
