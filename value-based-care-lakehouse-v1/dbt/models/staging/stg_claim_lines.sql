-- stg_claim_lines.sql
-- Claim line grain from DE-SynPUF Inpatient Claims. Only the Inpatient
-- file is wired up today - Outpatient and Carrier claims are not yet
-- implemented in ingestion/de_synpuf/land_de_synpuf.py (see that folder's
-- README "Not yet covered" section), so this staging model only reflects
-- inpatient claims for now.

select
    claim_line_bk,
    member_bk,
    provider_bk,
    cast(service_from_date as date) as service_from_date,
    cast(service_thru_date as date) as service_thru_date,
    cast(admission_date as date) as admission_date,
    cast(discharge_date as date) as discharge_date,
    drg_bk,
    cast(paid_amount as decimal(12,2)) as paid_amount,
    cast(primary_payer_paid_amount as decimal(12,2)) as primary_payer_paid_amount,
    cast(utilization_day_count as int) as utilization_day_count,
    'inpatient' as claim_type,
    record_source,
    load_dts
from {{ source('bronze', 'synpuf_inpatient_claim_header') }}
