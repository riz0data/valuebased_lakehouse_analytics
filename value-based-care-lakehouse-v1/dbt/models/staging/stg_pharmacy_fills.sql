-- stg_pharmacy_fills.sql
-- SYNTHETIC prescription fill transactions (member + drug + pharmacy +
-- fill_date + days_supply). See ingestion/pharmacy/README.md - there is
-- no public dataset of individual fill events.

select
    member_bk,
    drug_bk,
    pharmacy_bk,
    fill_date,
    days_supply,
    current_timestamp() as load_dts,
    'pharmacy_fills' as record_source
from {{ source('bronze', 'pharmacy_fills') }}
