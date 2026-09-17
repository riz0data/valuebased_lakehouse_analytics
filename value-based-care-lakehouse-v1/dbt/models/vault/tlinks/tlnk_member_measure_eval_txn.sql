-- tlnk_member_measure_eval_txn.sql
-- Transactional Link for member quality measure evaluation events - each
-- evaluation (met/not_met) as of an eval_date is an immutable,
-- point-in-time fact. SYNTHETIC results - see
-- ingestion/clinical_quality/README.md.

{{
    automate_dv.t_link(
        src_pk='member_measure_eval_txn_hk',
        src_fk=['member_hk', 'measure_hk'],
        src_payload=['eval_result', 'eval_date'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_member_measure_evals_hk'
    )
}}
