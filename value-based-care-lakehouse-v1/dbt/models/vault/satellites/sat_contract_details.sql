-- sat_contract_details.sql
-- Tracks VBC contract descriptive attributes over time. SYNTHETIC source
-- - see ingestion/payment_integrity/README.md.

{{
    automate_dv.sat(
        src_pk='contract_hk',
        src_hashdiff='contract_hashdiff',
        src_payload=['contract_model', 'effective_date'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_contracts_sat_hk'
    )
}}
