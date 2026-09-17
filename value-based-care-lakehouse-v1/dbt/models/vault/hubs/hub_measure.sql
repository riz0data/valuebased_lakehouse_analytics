-- hub_measure.sql
-- Hub for CMS Star Ratings quality measures. Real measure codes (BCS-E,
-- CBP, COL-E, D09, D10) - see ingestion/clinical_quality/README.md.

{{
    automate_dv.hub(
        src_pk='measure_hk',
        src_nk='measure_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_measures_hk'
    )
}}
