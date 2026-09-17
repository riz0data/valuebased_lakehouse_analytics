-- stg_claim_lines_sat_hk.sql
-- Hashing layer for sat_claim_details: descriptive/financial attributes
-- of the claim (dates, DRG, paid amount) tracked over time.

{% set yaml_metadata %}
source_model: 'stg_claim_lines'
hashed_columns:
  claim_line_hk: claim_line_bk
  claim_hashdiff:
    is_hashdiff: true
    columns:
      - service_from_date
      - service_thru_date
      - admission_date
      - discharge_date
      - drg_bk
      - paid_amount
      - primary_payer_paid_amount
      - utilization_day_count
      - claim_type
derived_columns:
  effective_from: load_dts
{% endset %}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
