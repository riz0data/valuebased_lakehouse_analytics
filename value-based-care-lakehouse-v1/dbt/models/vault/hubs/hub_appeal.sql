-- hub_appeal.sql
-- Hub for appeal cases. SYNTHETIC - see
-- ingestion/payment_integrity/README.md.

{{
    automate_dv.hub(
        src_pk='appeal_hk',
        src_nk='appeal_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_appeals_hk'
    )
}}
