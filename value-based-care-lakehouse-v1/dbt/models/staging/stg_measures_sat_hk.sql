-- stg_measures_sat_hk.sql
{% set yaml_metadata %}
source_model: 'stg_measures'
hashed_columns:
  measure_hk: measure_bk
  measure_hashdiff:
    is_hashdiff: true
    columns:
      - measure_name
      - measure_weight
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
