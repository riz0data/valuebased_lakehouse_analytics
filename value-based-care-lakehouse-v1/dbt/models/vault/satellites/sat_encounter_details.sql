-- sat_encounter_details.sql
-- Tracks encounter descriptive attributes over time. Real Synthea data.
-- Now includes encounter_end (discharge time for inpatient encounters),
-- needed for Readmission Rate.

{{
    automate_dv.sat(
        src_pk='encounter_hk',
        src_hashdiff='encounter_hashdiff',
        src_payload=['encounter_class_code', 'encounter_start', 'encounter_end'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounters_sat_hk'
    )
}}
