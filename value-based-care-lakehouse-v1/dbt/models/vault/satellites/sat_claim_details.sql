-- sat_claim_details.sql
-- Tracks claim-level descriptive and financial attributes over time:
-- service dates, DRG assignment, paid amounts, length of stay. This is
-- the Satellite that most "Ready Today" metrics in
-- docs/data-vault-model-reference.xlsx (Metrics sheet) read from.

{{
    automate_dv.sat(
        src_pk='claim_line_hk',
        src_hashdiff='claim_hashdiff',
        src_payload=['service_from_date', 'service_thru_date', 'admission_date',
                     'discharge_date', 'drg_bk', 'paid_amount',
                     'primary_payer_paid_amount', 'utilization_day_count', 'claim_type'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_claim_lines_sat_hk'
    )
}}
