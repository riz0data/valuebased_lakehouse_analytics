-- hub_authorization.sql
-- Hub for prior authorizations. SYNTHETIC - see
-- ingestion/payment_integrity/README.md.

{{
    automate_dv.hub(
        src_pk='authorization_hk',
        src_nk='authorization_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_authorizations_hk'
    )
}}
