-- lnk_member_suspected_hcc.sql
-- Links a member to an HCC category a suspecting engine has flagged as
-- plausible but not yet coded. This Link is additive beyond the
-- original ERD scope, built specifically to make HCC Capture Rate and
-- Suspecting Yield Rate computable - see
-- ingestion/risk_adjustment/README.md and
-- ingestion/risk_adjustment/make_risk_adjustment_sample.py
-- (make_suspected_hcc). SYNTHETIC.

{{
    automate_dv.link(
        src_pk='member_suspected_hcc_hk',
        src_fk=['member_hk', 'hcc_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_suspected_hcc_hk'
    )
}}
