-- lnk_member_pharmacy.sql
-- Links a member to each pharmacy they've used, derived from the
-- SYNTHETIC fill transactions - see ingestion/pharmacy/README.md.

{{
    automate_dv.link(
        src_pk='member_pharmacy_hk',
        src_fk=['member_hk', 'pharmacy_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_pharmacy_fills_hk'
    )
}}
