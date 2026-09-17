-- stg_pharmacies_hk.sql
{% set yaml_metadata %}
source_model: 'stg_pharmacies'
hashed_columns:
  pharmacy_hk: pharmacy_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
