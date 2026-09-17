-- hub_claim_line.sql
-- Hub for the claim line business entity, keyed on the DE-SynPUF claim ID.
-- Currently sourced from Inpatient Claims only - see
-- ingestion/de_synpuf/README.md "Not yet covered" for what's missing
-- (Outpatient, Carrier, Prescription Drug Events).

{{
    automate_dv.hub(
        src_pk='claim_line_hk',
        src_nk='claim_line_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_lines_hk'
    )
}}
