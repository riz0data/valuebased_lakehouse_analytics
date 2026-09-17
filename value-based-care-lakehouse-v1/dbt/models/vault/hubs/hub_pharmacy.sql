-- hub_pharmacy.sql
-- Hub for pharmacies, keyed on the real pharmacy NPI. Identified from
-- real NPPES data by NUCC taxonomy code 3336C0003X - see
-- ingestion/pharmacy/README.md.

{{
    automate_dv.hub(
        src_pk='pharmacy_hk',
        src_nk='pharmacy_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_pharmacies_hk'
    )
}}
