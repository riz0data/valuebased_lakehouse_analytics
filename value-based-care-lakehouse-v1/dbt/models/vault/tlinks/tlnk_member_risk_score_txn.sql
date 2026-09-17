-- tlnk_member_risk_score_txn.sql
-- Transactional Link for member RAF score events, one per member per
-- model year - each year's risk score calculation is an immutable,
-- point-in-time fact. SYNTHETIC values - see
-- ingestion/risk_adjustment/README.md.

{{
    automate_dv.t_link(
        src_pk='member_risk_score_txn_hk',
        src_fk=['member_hk', 'risk_model_hk'],
        src_payload=['raf_score', 'model_year'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_member_risk_scores_hk'
    )
}}
