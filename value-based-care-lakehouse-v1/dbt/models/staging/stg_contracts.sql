-- stg_contracts.sql
-- SYNTHETIC VBC contract fixtures - see ingestion/payment_integrity/README.md.

select
    contract_bk,
    contract_model,
    cast(effective_date as date) as effective_date,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_contracts') }}
