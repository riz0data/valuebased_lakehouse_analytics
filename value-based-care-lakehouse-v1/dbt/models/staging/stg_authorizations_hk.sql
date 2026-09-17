-- stg_authorizations_hk.sql
-- Computes authorization_hk plus the component hashkeys
-- (claim_line_hk) needed by lnk_claim_authorization.

{% set yaml_metadata %}
source_model: 'stg_authorizations'
hashed_columns:
  authorization_hk: authorization_bk
  claim_line_hk: claim_line_bk
  claim_authorization_hk:
    - claim_line_bk
    - authorization_bk
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
