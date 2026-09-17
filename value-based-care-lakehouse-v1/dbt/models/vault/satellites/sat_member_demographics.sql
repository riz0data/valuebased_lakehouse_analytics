-- sat_member_demographics.sql
-- Tracks member demographic attributes over time. Source system is
-- disjoint per member (DE-SynPUF or Synthea, never both for the same
-- member_bk), so hashdiff-based change detection here mainly guards
-- against re-processing the same source file, rather than reconciling
-- conflicting updates across systems.

{{
    automate_dv.sat(
        src_pk='member_hk',
        src_hashdiff='member_hashdiff',
        src_payload=['birth_date', 'sex', 'race_code', 'state_code'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_members_sat_hk'
    )
}}
