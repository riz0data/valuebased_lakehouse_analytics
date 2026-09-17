-- stg_providers_sat_hk.sql
-- Hashing layer for sat_provider_details.

{% set yaml_metadata %}
source_model: 'stg_providers'
hashed_columns:
  provider_hk: provider_bk
  provider_hashdiff:
    is_hashdiff: true
    columns:
      - provider_first_name
      - provider_last_name
      - provider_credential
      - primary_taxonomy_code
      - practice_state
      - practice_city
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
