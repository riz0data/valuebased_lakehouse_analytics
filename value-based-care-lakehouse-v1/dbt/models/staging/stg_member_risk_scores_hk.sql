-- stg_member_risk_scores_hk.sql
-- T-Link hash staging. Derives effective_from from the transaction's
-- own business date (model_year -> Jan 1 of that year), following the
-- same pattern established for the Payment Integrity T-Links (a
-- dedicated derived column, not a raw payload column referenced
-- directly - see dbt/models/vault/tlinks/README.md).
{% set yaml_metadata %}
source_model: 'stg_member_risk_scores'
hashed_columns:
  member_hk: member_bk
  risk_model_hk: risk_model_bk
  member_risk_score_txn_hk:
    - member_bk
    - risk_model_bk
    - model_year
derived_columns:
  effective_from: "cast(cast(model_year as string) || '-01-01' as date)"
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
