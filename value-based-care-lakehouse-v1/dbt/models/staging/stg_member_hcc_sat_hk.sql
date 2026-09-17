-- stg_member_hcc_sat_hk.sql
-- Drives SAT_MEMBER_HCC_STATUS per the ERD. Now includes the real
-- coding-gap lifecycle fields the synthetic generator emits
-- (active_flag, coding_gap_identified_date, coding_gap_closed_date) -
-- see ingestion/risk_adjustment/README.md.
{% set yaml_metadata %}
source_model: 'stg_member_hcc'
hashed_columns:
  member_hk: member_bk
  hcc_hk: hcc_bk
  member_hcc_hk:
    - member_bk
    - hcc_bk
  member_hcc_status_hashdiff:
    is_hashdiff: true
    columns:
      - active_flag
      - coding_gap_identified_date
      - coding_gap_closed_date
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
