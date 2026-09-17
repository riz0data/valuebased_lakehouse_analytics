-- tlnk_cob_recovery_txn.sql
-- Transactional Link for Coordination-of-Benefits recovery events (money
-- recovered from a secondary payer after initial adjudication). SYNTHETIC
-- source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.t_link(
        src_pk='cob_recovery_txn_hk',
        src_fk=['claim_line_hk'],
        src_payload=['recovery_amount', 'recovery_date'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_cob_recovery_txns_hk'
    )
}}
