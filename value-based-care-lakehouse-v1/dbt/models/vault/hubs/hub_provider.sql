-- hub_provider.sql
-- Hub for individual providers, keyed on NPI (NPPES).

{{
    automate_dv.hub(
        src_pk='provider_hk',
        src_nk='provider_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_providers_hk'
    )
}}
