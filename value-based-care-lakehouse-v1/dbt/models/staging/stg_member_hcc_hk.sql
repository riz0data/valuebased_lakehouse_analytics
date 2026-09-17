-- stg_member_hcc_hk.sql
-- Computes the composite Link hash key plus its 2 component FK hash
-- keys (member, hcc), matching hub_member's existing hash key
-- computation (member_bk) so the Link resolves correctly against the
-- Core-domain hub_member built previously.
{% set yaml_metadata %}
source_model: 'stg_member_hcc'
hashed_columns:
  member_hk: member_bk
  hcc_hk: hcc_bk
  member_hcc_hk:
    - member_bk
    - hcc_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
