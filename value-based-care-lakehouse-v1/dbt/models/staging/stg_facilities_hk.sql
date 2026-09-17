-- stg_facilities_hk.sql
-- Hashing layer on top of stg_facilities: computes facility_hk.

{% set yaml_metadata %}
source_model: 'stg_facilities'
hashed_columns:
  facility_hk: facility_bk
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
