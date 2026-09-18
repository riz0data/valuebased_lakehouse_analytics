-- stg_procedures_sat_hk.sql
-- NOTE: DE-SynPUF only provides bare ICD-9 procedure codes, not
-- descriptions - a real deployment would enrich this via a reference
-- crosswalk (e.g. CMS ICD-9-CM procedure code descriptions file) before
-- this satellite. Tracking coding_system as the payload for now so the
-- Satellite pattern is structurally correct and demonstrable; see
-- ingestion/payment_integrity/README.md.

{% set yaml_metadata %}
source_model: 'stg_procedures'
hashed_columns:
  procedure_hk: procedure_bk
  procedure_hashdiff:
    is_hashdiff: true
    columns:
      - coding_system
derived_columns:
  effective_from: load_dts
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
