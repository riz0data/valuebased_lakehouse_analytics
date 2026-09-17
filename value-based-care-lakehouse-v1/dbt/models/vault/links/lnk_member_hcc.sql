-- lnk_member_hcc.sql
-- Links a member to the HCC categories they're assigned. SYNTHETIC
-- assignment - see ingestion/risk_adjustment/README.md.

{{
    automate_dv.link(
        src_pk='member_hcc_hk',
        src_fk=['member_hk', 'hcc_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_member_hcc_hk'
    )
}}
