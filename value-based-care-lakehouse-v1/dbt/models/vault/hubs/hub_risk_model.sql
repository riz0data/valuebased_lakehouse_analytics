-- hub_risk_model.sql
-- Hub for CMS-HCC model versions (V24, V28) - real, CMS-published model
-- versions. See ingestion/risk_adjustment/README.md.

{{
    automate_dv.hub(
        src_pk='risk_model_hk',
        src_nk='risk_model_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_risk_models_hk'
    )
}}
