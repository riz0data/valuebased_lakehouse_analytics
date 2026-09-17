-- lnk_claim_appeal.sql
-- Links a claim to its appeal case, where one exists. SYNTHETIC source -
-- see ingestion/payment_integrity/README.md.

{{
    automate_dv.link(
        src_pk='claim_appeal_hk',
        src_fk=['claim_line_hk', 'appeal_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_appeals_hk'
    )
}}
