-- lnk_diagnosis_hcc_crosswalk.sql
-- Links a diagnosis code to its HCC category under a specific risk
-- model version - a 3-way Link, since the same diagnosis can map to
-- different HCCs (or none) depending on model version (V24 vs V28).
-- Illustrative sample crosswalk, not the full CMS mapping table - see
-- ingestion/risk_adjustment/README.md.

{{
    automate_dv.link(
        src_pk='diagnosis_hcc_crosswalk_hk',
        src_fk=['diagnosis_hk', 'hcc_hk', 'risk_model_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_diagnosis_hcc_crosswalk_hk'
    )
}}
