-- stg_drugs_sat_hk.sql
{% set yaml_metadata %}
source_model: 'stg_drugs'
hashed_columns:
  drug_hk: drug_bk
  drug_hashdiff:
    is_hashdiff: true
    columns:
      - drug_name
      - drug_class
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
