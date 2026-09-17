-- tlnk_claim_payment_txn.sql
-- Transactional Link for claim payment events: billed/allowed/paid
-- amounts as of a payment date. Append-only fact - each payment event is
-- immutable once recorded, unlike a Link's durable relationship. SYNTHETIC
-- source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.t_link(
        src_pk='payment_txn_hk',
        src_fk=['claim_line_hk'],
        src_payload=['billed_amount', 'allowed_amount', 'paid_amount', 'payment_date'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_payment_txns_hk'
    )
}}
