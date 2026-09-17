-- stg_provider_contracts.sql
-- SYNTHETIC provider-to-contract attachment bridge.

select
    provider_bk,
    contract_bk,
    'payment_integrity_synthetic' as record_source,
    current_timestamp() as load_dts
from {{ source('bronze', 'pi_provider_contracts') }}
