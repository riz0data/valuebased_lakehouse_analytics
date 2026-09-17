-- lnk_provider_contract.sql
-- Links a provider to the VBC contract(s) they participate in. SYNTHETIC
-- source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.link(
        src_pk='provider_contract_hk',
        src_fk=['provider_hk', 'contract_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_provider_contracts_hk'
    )
}}
