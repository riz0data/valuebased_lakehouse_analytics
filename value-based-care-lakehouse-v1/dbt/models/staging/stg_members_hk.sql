-- stg_members_hk.sql
-- Hashing layer on top of stg_members: computes member_hk via automate_dv's
-- stage() macro so hub_member (and any future member-grain Satellite) can
-- reference a pre-computed hash key rather than hashing inline.

{% set yaml_metadata %}
source_model: 'stg_members'
hashed_columns:
  member_hk: member_bk
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
