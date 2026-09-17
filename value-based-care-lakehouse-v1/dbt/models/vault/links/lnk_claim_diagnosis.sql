-- lnk_claim_diagnosis.sql
-- Links each claim line to every diagnosis code recorded on it. Grain:
-- one row per (claim, diagnosis) pair - already unpivoted at the
-- ingestion layer (see ingestion/de_synpuf/land_de_synpuf.py). Sourced
-- from stg_claim_diagnoses_hk.

{{
    automate_dv.link(
        src_pk='claim_diagnosis_hk',
        src_fk=['claim_line_hk', 'diagnosis_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_diagnoses_hk'
    )
}}
