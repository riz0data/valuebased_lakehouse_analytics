-- stg_diagnoses_hk.sql
-- Hashing layer on top of stg_diagnoses: computes diagnosis_hk.

{% set yaml_metadata %}
source_model: 'stg_diagnoses'
hashed_columns:
  diagnosis_hk: diagnosis_bk
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
