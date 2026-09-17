-- sat_risk_model_details.sql
-- Tracks risk model descriptive attributes over time. Real CMS-HCC
-- model version names.

{{
    automate_dv.sat(
        src_pk='risk_model_hk',
        src_hashdiff='risk_model_hashdiff',
        src_payload=['model_name'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_risk_models_sat_hk'
    )
}}
