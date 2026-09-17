-- dim_provider.sql
-- Conformed Provider dimension, built from hub_provider + sat_provider_details.

select
    h.provider_hk,
    h.provider_bk as provider_npi,
    s.provider_first_name,
    s.provider_last_name,
    s.provider_credential,
    s.primary_taxonomy_code,
    s.practice_state,
    s.practice_city
from {{ ref('hub_provider') }} h
left join {{ ref('sat_provider_details') }} s
    on h.provider_hk = s.provider_hk
