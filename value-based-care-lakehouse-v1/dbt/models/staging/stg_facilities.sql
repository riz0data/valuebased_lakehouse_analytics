-- stg_facilities.sql
-- Organizations/facilities from NPPES (Entity Type Code 2).

select
    npi as facility_bk,
    organization_name,
    practice_state,
    practice_city,
    primary_taxonomy_code,
    record_source,
    load_dts
from {{ source('bronze', 'nppes_facilities') }}
