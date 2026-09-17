-- stg_pharmacies_sat_hk.sql
{% set yaml_metadata %}
source_model: 'stg_pharmacies'
hashed_columns:
  pharmacy_hk: pharmacy_bk
  pharmacy_hashdiff:
    is_hashdiff: true
    columns:
      - pharmacy_name
      - pharmacy_type
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
