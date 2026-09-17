-- stg_encounters_hk.sql
-- Computes the Hub hash key for the Encounter itself, plus the FK hash
-- keys needed by lnk_member_encounter, lnk_encounter_provider, and
-- lnk_encounter_facility. provider_bk/facility_bk are hashed the same
-- way hub_provider/hub_facility already hash them (provider_bk /
-- facility_bk directly), so these Links resolve correctly against the
-- Core-domain Hubs built previously.
{% set yaml_metadata %}
source_model: 'stg_encounters'
hashed_columns:
  encounter_hk: encounter_bk
  member_hk: member_bk
  provider_hk: provider_bk
  facility_hk: facility_bk
  member_encounter_hk:
    - member_bk
    - encounter_bk
  encounter_provider_hk:
    - encounter_bk
    - provider_bk
  encounter_facility_hk:
    - encounter_bk
    - facility_bk
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns']) }}
