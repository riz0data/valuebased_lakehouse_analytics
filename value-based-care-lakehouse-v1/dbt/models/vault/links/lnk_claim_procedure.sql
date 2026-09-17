-- lnk_claim_procedure.sql
-- Links each claim line to every procedure code recorded on it. Grain:
-- one row per (claim, procedure) pair, unpivoted at ingestion time.

{{
    automate_dv.link(
        src_pk='claim_procedure_hk',
        src_fk=['claim_line_hk', 'procedure_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_procedures_hk'
    )
}}
