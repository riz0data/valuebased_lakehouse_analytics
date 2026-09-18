-- stg_adjustment_txns_hk.sql
{% set yaml_metadata %}
source_model: 'stg_adjustment_txns'
hashed_columns:
  adjustment_txn_hk: txn_bk
  claim_line_hk: claim_line_bk
derived_columns:
  effective_from: adjustment_date
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
