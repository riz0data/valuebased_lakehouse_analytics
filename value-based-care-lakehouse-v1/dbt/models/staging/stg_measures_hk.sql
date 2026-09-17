-- stg_measures_hk.sql
{% set yaml_metadata %}
source_model: 'stg_measures'
hashed_columns:
  measure_hk: measure_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
