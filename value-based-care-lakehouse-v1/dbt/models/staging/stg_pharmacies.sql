-- stg_pharmacies.sql
-- Pharmacies, identified from real NPPES facility/organization data by
-- their real NUCC provider taxonomy code, 3336C0003X (Community/Retail
-- Pharmacy). No new ingestion needed - this filters the same
-- nppes_facilities bronze table that feeds stg_facilities/hub_facility.
-- See ingestion/pharmacy/README.md.

select
    npi as pharmacy_bk,
    organization_name as pharmacy_name,
    primary_taxonomy_code as pharmacy_type,
    record_source,
    load_dts
from {{ source('bronze', 'nppes_facilities') }}
where primary_taxonomy_code = '3336C0003X'
