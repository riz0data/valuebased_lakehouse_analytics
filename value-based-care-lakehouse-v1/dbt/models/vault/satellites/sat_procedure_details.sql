-- sat_procedure_details.sql
-- Tracks procedure descriptive attributes. Currently limited to
-- coding_system since DE-SynPUF only provides bare ICD-9 procedure codes,
-- not descriptions - see stg_procedures_sat_hk.sql and
-- ingestion/payment_integrity/README.md for the enrichment gap.

{{
    automate_dv.sat(
        src_pk='procedure_hk',
        src_hashdiff='procedure_hashdiff',
        src_payload=['coding_system'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_procedures_sat_hk'
    )
}}
