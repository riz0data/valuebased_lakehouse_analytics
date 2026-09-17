-- lnk_member_encounter.sql
-- Links a member to each encounter they had. Real Synthea data.

{{
    automate_dv.link(
        src_pk='member_encounter_hk',
        src_fk=['member_hk', 'encounter_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounters_hk'
    )
}}
