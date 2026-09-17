-- stg_hcc_categories_sat_hk.sql
{% set yaml_metadata %}
source_model: 'stg_hcc_categories'
hashed_columns:
  hcc_hk: hcc_bk
  hcc_hashdiff:
    is_hashdiff: true
    columns:
      - hcc_description
      - hcc_weight
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
