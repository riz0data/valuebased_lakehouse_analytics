-- hub_diagnosis.sql
-- Hub for diagnosis codes, conformed across ICD-9 (DE-SynPUF) and SNOMED
-- (Synthea) coding systems - see stg_diagnoses.sql for why these are not
-- cross-walked to a single system in this repo.

{{
    automate_dv.hub(
        src_pk='diagnosis_hk',
        src_nk='diagnosis_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_diagnoses_hk'
    )
}}
