-- stg_drgs_sat_hk.sql
-- Hashdiff now covers the real drg_description/drg_relative_weight
-- fields brought in by stg_drgs.sql's join to the illustrative CMS
-- MS-DRG weight reference table - see
-- ingestion/payment_integrity/reference_data/drg_weights.csv and
-- ingestion/payment_integrity/README.md.

{% set yaml_metadata %}
source_model: 'stg_drgs'
hashed_columns:
  drg_hk: drg_bk
  drg_hashdiff:
    is_hashdiff: true
    columns:
      - drg_bk
      - drg_description
      - drg_relative_weight
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
