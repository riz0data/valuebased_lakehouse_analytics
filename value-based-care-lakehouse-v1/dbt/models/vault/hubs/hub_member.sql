-- hub_member.sql
-- Hub for the conformed Member business entity, sourced from both
-- DE-SynPUF beneficiaries and Synthea patients (see stg_members.sql,
-- hashed in stg_members_hk.sql). One of the conformed shared Hubs
-- described in ADR-003 - deliberately NOT split by source system, since
-- Payment Integrity, Risk Adjustment, and Clinical Quality all need to
-- join back to the same member_hk to compute cross-domain metrics like
-- Net VBC Contract Value.

{{
    automate_dv.hub(
        src_pk='member_hk',
        src_nk='member_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_members_hk'
    )
}}
