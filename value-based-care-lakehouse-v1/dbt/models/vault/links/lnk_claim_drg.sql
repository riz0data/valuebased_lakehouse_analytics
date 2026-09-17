-- lnk_claim_drg.sql
-- Links each claim line to its assigned DRG. Grain: one row per claim
-- (a claim has at most one DRG assignment in DE-SynPUF Inpatient Claims).

{{
    automate_dv.link(
        src_pk='claim_drg_hk',
        src_fk=['claim_line_hk', 'drg_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_drg_hk'
    )
}}
