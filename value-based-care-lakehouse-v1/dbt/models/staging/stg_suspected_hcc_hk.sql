-- stg_suspected_hcc_hk.sql
{% set yaml_metadata %}
source_model: 'stg_suspected_hcc'
hashed_columns:
  member_hk: member_bk
  hcc_hk: hcc_bk
  member_suspected_hcc_hk:
    - member_bk
    - hcc_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
