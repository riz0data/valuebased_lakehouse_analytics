-- stg_claim_procedures_hk.sql
{% set yaml_metadata %}
source_model: 'stg_claim_procedures'
hashed_columns:
  claim_line_hk: claim_line_bk
  procedure_hk: procedure_bk
  claim_procedure_hk:
    - claim_line_bk
    - procedure_bk
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
