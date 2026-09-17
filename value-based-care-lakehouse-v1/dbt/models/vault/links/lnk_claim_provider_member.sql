-- lnk_claim_provider_member.sql
-- Links a claim line to the provider who rendered it and the member it
-- was billed for. Grain: one row per claim line (each inpatient claim
-- has exactly one billing provider in DE-SynPUF). Sourced from
-- stg_claim_lines_hk, which computes all three component hashkeys plus
-- the composite claim_provider_member_hk.

{{
    automate_dv.link(
        src_pk='claim_provider_member_hk',
        src_fk=['claim_line_hk', 'provider_hk', 'member_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_lines_hk'
    )
}}
