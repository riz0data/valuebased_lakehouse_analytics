-- tlnk_claim_adjustment_txn.sql
-- Transactional Link for claim adjustment events (e.g. contractual
-- write-offs, coding denials) - each adjustment is a discrete, immutable
-- event on a claim. SYNTHETIC source - see
-- ingestion/payment_integrity/README.md.

{{
    automate_dv.t_link(
        src_pk='adjustment_txn_hk',
        src_fk=['claim_line_hk'],
        src_payload=['adjustment_amount', 'adjustment_reason_code', 'adjustment_date'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_adjustment_txns_hk'
    )
}}
