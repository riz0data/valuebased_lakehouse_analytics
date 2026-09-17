-- stg_members_sat_hk.sql
-- Hashing layer for sat_member_demographics: computes member_hk (to join
-- back to the Hub) plus a hashdiff over the descriptive attributes, so
-- automate_dv's sat() macro can detect when a member's demographic
-- attributes have changed between loads.

{% set yaml_metadata %}
source_model: 'stg_members'
hashed_columns:
  member_hk: member_bk
  member_hashdiff:
    is_hashdiff: true
    columns:
      - birth_date
      - sex
      - race_code
      - state_code
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
