-- stg_claim_diagnoses_hk.sql
-- Hashing layer on top of stg_claim_diagnoses (the unpivoted claim x
-- diagnosis bridge from ingestion): computes claim_line_hk, diagnosis_hk,
-- and the composite claim_diagnosis_hk for lnk_claim_diagnosis.

{% set yaml_metadata %}
source_model: 'stg_claim_diagnoses'
hashed_columns:
  claim_line_hk: claim_line_bk
  diagnosis_hk: diagnosis_bk
  claim_diagnosis_hk:
    - claim_line_bk
    - diagnosis_bk
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
