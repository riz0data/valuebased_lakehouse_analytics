-- stg_encounter_diagnoses_hk.sql
-- Computes the composite Link hash key plus its 2 component FK hash
-- keys (encounter, diagnosis) for lnk_encounter_diagnosis.
{% set yaml_metadata %}
source_model: 'stg_encounter_diagnoses'
hashed_columns:
  encounter_hk: encounter_bk
  diagnosis_hk: diagnosis_bk
  encounter_diagnosis_hk:
    - encounter_bk
    - diagnosis_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
