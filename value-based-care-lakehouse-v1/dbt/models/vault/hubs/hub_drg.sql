-- hub_drg.sql
-- Hub for DRG (Diagnosis-Related Group) codes. Sourced from the real
-- CLM_DRG_CD field on DE-SynPUF Inpatient Claims - genuine CMS data,
-- no synthetic fixture needed here.

{{
    automate_dv.hub(
        src_pk='drg_hk',
        src_nk='drg_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_drgs_hk'
    )
}}
