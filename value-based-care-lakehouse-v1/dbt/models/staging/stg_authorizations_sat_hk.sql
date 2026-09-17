-- stg_authorizations_sat_hk.sql
{% set yaml_metadata %}
source_model: 'stg_authorizations'
hashed_columns:
  authorization_hk: authorization_bk
  authorization_hashdiff:
    is_hashdiff: true
    columns:
      - auth_status
      - requested_date
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
