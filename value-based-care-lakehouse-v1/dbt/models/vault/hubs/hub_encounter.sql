-- hub_encounter.sql
-- Hub for clinical encounters. Real Synthea encounter data - see
-- ingestion/synthea/land_synthea.py.

{{
    automate_dv.hub(
        src_pk='encounter_hk',
        src_nk='encounter_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounters_hk'
    )
}}
