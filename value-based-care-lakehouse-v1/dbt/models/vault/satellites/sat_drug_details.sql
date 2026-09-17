-- sat_drug_details.sql
-- Tracks drug descriptive attributes over time. Real FDA NDC Directory
-- data.

{{
    automate_dv.sat(
        src_pk='drug_hk',
        src_hashdiff='drug_hashdiff',
        src_payload=['drug_name', 'drug_class'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_drugs_sat_hk'
    )
}}
