-- stg_member_measure_hk.sql
-- Computes the composite Link hash key plus its 2 component FK hash
-- keys (member, measure) for lnk_member_measure.
{% set yaml_metadata %}
source_model: 'stg_member_measure'
hashed_columns:
  member_hk: member_bk
  measure_hk: measure_bk
  member_measure_hk:
    - member_bk
    - measure_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
