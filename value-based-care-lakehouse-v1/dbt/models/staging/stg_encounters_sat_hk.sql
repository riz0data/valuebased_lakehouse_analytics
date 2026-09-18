-- stg_encounters_sat_hk.sql
-- Hashdiff now also covers encounter_end, needed for Readmission Rate
-- (discharge date on inpatient encounters).
{% set yaml_metadata %}
source_model: 'stg_encounters'
hashed_columns:
  encounter_hk: encounter_bk
  encounter_hashdiff:
    is_hashdiff: true
    columns:
      - encounter_class_code
      - encounter_start
      - encounter_end
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
