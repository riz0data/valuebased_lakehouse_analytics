-- sat_pharmacy_details.sql
-- Tracks pharmacy descriptive attributes over time. Real NPPES data.

{{
    automate_dv.sat(
        src_pk='pharmacy_hk',
        src_hashdiff='pharmacy_hashdiff',
        src_payload=['pharmacy_name', 'pharmacy_type'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_pharmacies_sat_hk'
    )
}}
