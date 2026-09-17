-- sat_appeal_details.sql
-- Tracks appeal case status over time (e.g. pending -> upheld/overturned).
-- SYNTHETIC source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.sat(
        src_pk='appeal_hk',
        src_hashdiff='appeal_hashdiff',
        src_payload=['appeal_status', 'appeal_reason'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_appeals_sat_hk'
    )
}}
