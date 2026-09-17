-- sat_measure_definition.sql
-- Tracks quality measure descriptive attributes over time. Real CMS
-- Star Ratings measure names; weight values are illustrative, not the
-- official CMS weighting table. See ingestion/clinical_quality/README.md.

{{
    automate_dv.sat(
        src_pk='measure_hk',
        src_hashdiff='measure_hashdiff',
        src_payload=['measure_name', 'measure_weight'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_measures_sat_hk'
    )
}}
