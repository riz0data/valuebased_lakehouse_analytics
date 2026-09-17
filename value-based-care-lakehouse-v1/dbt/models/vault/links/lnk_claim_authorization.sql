-- lnk_claim_authorization.sql
-- Links a claim to its prior authorization, where one exists. SYNTHETIC
-- source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.link(
        src_pk='claim_authorization_hk',
        src_fk=['claim_line_hk', 'authorization_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_authorizations_hk'
    )
}}
