-- stg_contracts_hk.sql
{% set yaml_metadata %}
source_model: 'stg_contracts'
hashed_columns:
  contract_hk: contract_bk
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
