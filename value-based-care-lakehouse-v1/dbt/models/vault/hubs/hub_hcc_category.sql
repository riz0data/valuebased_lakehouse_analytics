-- hub_hcc_category.sql
-- Hub for CMS-HCC categories. Category codes/descriptions are REAL
-- (representative subset of the CMS-HCC V28 model) - see
-- ingestion/risk_adjustment/README.md.

{{
    automate_dv.hub(
        src_pk='hcc_hk',
        src_nk='hcc_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_hcc_categories_hk'
    )
}}
