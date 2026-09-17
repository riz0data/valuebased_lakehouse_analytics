-- stg_member_measure_evals_hk.sql
-- T-Link hash staging. Derives effective_from from the eval's own
-- eval_date, following the same pattern established for Payment
-- Integrity and Risk Adjustment T-Links (a dedicated derived column,
-- not a raw payload column referenced directly).
{% set yaml_metadata %}
source_model: 'stg_member_measure_evals'
hashed_columns:
  member_hk: member_bk
  measure_hk: measure_bk
  member_measure_eval_txn_hk:
    - member_bk
    - measure_bk
    - eval_date
derived_columns:
  effective_from: eval_date
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
