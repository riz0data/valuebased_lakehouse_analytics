-- stg_diagnosis_hcc_crosswalk_hk.sql
-- Computes the composite Link hash key plus its 3 component FK hash
-- keys (diagnosis, hcc, risk_model), matching hub_diagnosis's existing
-- hash key computation (diagnosis_bk) so the Link resolves correctly
-- against the Core-domain hub_diagnosis built previously.
{% set yaml_metadata %}
source_model: 'stg_diagnosis_hcc_crosswalk'
hashed_columns:
  diagnosis_hk: diagnosis_bk
  hcc_hk: hcc_bk
  risk_model_hk: risk_model_bk
  diagnosis_hcc_crosswalk_hk:
    - diagnosis_bk
    - hcc_bk
    - risk_model_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
