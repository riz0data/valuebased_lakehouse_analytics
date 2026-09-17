-- lnk_encounter_diagnosis.sql
-- Links an encounter to each diagnosis (condition) recorded on it. Real
-- Synthea data - diagnosis codes here are SNOMED CT, unioned at
-- hub_diagnosis with DE-SynPUF's ICD-9 codes without cross-walking (see
-- stg_diagnoses.sql).

{{
    automate_dv.link(
        src_pk='encounter_diagnosis_hk',
        src_fk=['encounter_hk', 'diagnosis_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounter_diagnoses_hk'
    )
}}
