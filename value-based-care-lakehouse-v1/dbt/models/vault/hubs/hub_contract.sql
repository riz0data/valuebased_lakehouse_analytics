-- hub_contract.sql
-- Hub for Value-Based Care contracts. SYNTHETIC - see
-- ingestion/payment_integrity/README.md. No open dataset exists for
-- managed-care contract terms.

{{
    automate_dv.hub(
        src_pk='contract_hk',
        src_nk='contract_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_contracts_hk'
    )
}}
