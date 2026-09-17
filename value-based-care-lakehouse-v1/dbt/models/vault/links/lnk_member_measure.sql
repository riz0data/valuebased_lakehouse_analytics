-- lnk_member_measure.sql
-- Links a member to the quality measures they're eligible for.
-- SYNTHETIC assignment - see ingestion/clinical_quality/README.md.

{{
    automate_dv.link(
        src_pk='member_measure_hk',
        src_fk=['member_hk', 'measure_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_member_measure_hk'
    )
}}
