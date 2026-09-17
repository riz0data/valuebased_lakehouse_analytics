-- stg_appeals_hk.sql
-- Computes appeal_hk plus the component hashkeys (claim_line_hk) needed
-- by lnk_claim_appeal.

{% set yaml_metadata %}
source_model: 'stg_appeals'
hashed_columns:
  appeal_hk: appeal_bk
  claim_line_hk: claim_line_bk
  claim_appeal_hk:
    - claim_line_bk
    - appeal_bk
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
