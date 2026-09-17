-- stg_payment_txns.sql
-- SYNTHETIC claim payment transaction fixtures.

select
    txn_bk,
    claim_line_bk,
    cast(billed_amount as decimal(12,2)) as billed_amount,
    cast(allowed_amount as decimal(12,2)) as allowed_amount,
    cast(paid_amount as decimal(12,2)) as paid_amount,
    cast(payment_date as date) as payment_date,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_payment_transactions') }}
