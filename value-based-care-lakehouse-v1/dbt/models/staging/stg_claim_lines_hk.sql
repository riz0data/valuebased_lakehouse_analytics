-- stg_claim_lines_hk.sql
-- Hashing layer on top of stg_claim_lines: computes claim_line_hk plus
-- the composite claim_provider_member_hk used by lnk_claim_provider_member.
-- This single staged model feeds both hub_claim_line and the link, which
-- is the standard automate_dv pattern - one hashed staging model can serve
-- multiple Vault structures as long as all needed hashkeys are computed here.

{% set yaml_metadata %}
source_model: 'stg_claim_lines'
hashed_columns:
  claim_line_hk: claim_line_bk
  provider_hk: provider_bk
  member_hk: member_bk
  claim_provider_member_hk:
    - claim_line_bk
    - provider_bk
    - member_bk
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
