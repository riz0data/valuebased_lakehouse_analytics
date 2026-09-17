-- stg_cob_recovery_txns.sql
-- SYNTHETIC coordination-of-benefits recovery transaction fixtures.

select
    txn_bk,
    claim_line_bk,
    cast(recovery_amount as decimal(12,2)) as recovery_amount,
    cast(recovery_date as date) as recovery_date,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_cob_recovery_transactions') }}
