-- sat_authorization_details.sql
-- Tracks prior authorization status over time (e.g. pending -> approved).
-- SYNTHETIC source - see ingestion/payment_integrity/README.md.

{{
    automate_dv.sat(
        src_pk='authorization_hk',
        src_hashdiff='authorization_hashdiff',
        src_payload=['auth_status', 'requested_date'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_authorizations_sat_hk'
    )
}}
