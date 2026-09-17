-- sat_hcc_category_details.sql
-- Tracks HCC category descriptive attributes over time. Real category
-- codes/descriptions; weight values are illustrative, not the official
-- CMS relative factor table - see ingestion/risk_adjustment/README.md.

{{
    automate_dv.sat(
        src_pk='hcc_hk',
        src_hashdiff='hcc_hashdiff',
        src_payload=['hcc_description', 'hcc_weight'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_hcc_categories_sat_hk'
    )
}}
