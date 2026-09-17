-- lnk_pharmacy_drug.sql
-- Links a pharmacy to each drug it has dispensed, derived from the
-- SYNTHETIC fill transactions - see ingestion/pharmacy/README.md.

{{
    automate_dv.link(
        src_pk='pharmacy_drug_hk',
        src_fk=['pharmacy_hk', 'drug_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_pharmacy_fills_hk'
    )
}}
