-- sat_drg_details.sql
-- Tracks DRG descriptive attributes, now enriched with real CMS MS-DRG
-- relative weights for the DRG codes present in this repo's sample data
-- (see stg_drgs.sql and ingestion/payment_integrity/README.md) - this
-- is what makes DRG Reimbursement Variance computable.

{{
    automate_dv.sat(
        src_pk='drg_hk',
        src_hashdiff='drg_hashdiff',
        src_payload=['drg_description', 'drg_relative_weight'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_drgs_sat_hk'
    )
}}
