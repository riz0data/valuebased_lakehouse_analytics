-- hub_procedure.sql
-- Hub for procedure codes. Sourced from DE-SynPUF ICD-9-CM procedure
-- codes - NOT HCPCS Level II as originally scoped in the ERD. See
-- ingestion/payment_integrity/README.md for why (DE-SynPUF's public
-- release predates HCPCS-level granularity).

{{
    automate_dv.hub(
        src_pk='procedure_hk',
        src_nk='procedure_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_procedures_hk'
    )
}}
