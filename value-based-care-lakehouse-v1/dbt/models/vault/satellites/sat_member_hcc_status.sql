-- sat_member_hcc_status.sql
-- Tracks each member-HCC assignment's coding-gap lifecycle over time:
-- whether it's currently active/closed (active_flag) and when the gap
-- was identified/closed. SYNTHETIC source, now with real lifecycle
-- dates emitted by the generator - see
-- ingestion/risk_adjustment/README.md.

{{
    automate_dv.sat(
        src_pk='member_hcc_hk',
        src_hashdiff='member_hcc_status_hashdiff',
        src_payload=['active_flag', 'coding_gap_identified_date', 'coding_gap_closed_date'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_member_hcc_sat_hk'
    )
}}
