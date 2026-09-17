-- stg_providers.sql
-- Individual providers from NPPES (Entity Type Code 1). See
-- ingestion/nppes/nppes_schema.py for the raw-to-staging column mapping
-- already applied at ingestion time - this model just aliases the
-- business key to a consistent name and passes fields through.

select
    npi as provider_bk,
    provider_first_name,
    provider_last_name,
    provider_credential,
    primary_taxonomy_code,
    practice_state,
    practice_city,
    record_source,
    load_dts
from {{ source('bronze', 'nppes_providers') }}
