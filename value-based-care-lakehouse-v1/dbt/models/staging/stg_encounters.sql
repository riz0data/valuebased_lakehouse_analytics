-- stg_encounters.sql
-- Real Synthea encounter data (patients, providers, facilities, dates).
-- See ingestion/synthea/land_synthea.py - provider_reference and
-- facility_reference were added to the Synthea Encounter field map
-- specifically to support this domain (see ingestion/synthea/README.md).

select
    encounter_bk,
    member_reference as member_bk,
    provider_reference as provider_bk,
    facility_reference as facility_bk,
    encounter_status,
    encounter_class_code,
    encounter_type_text,
    cast(encounter_start as timestamp) as encounter_start,
    cast(encounter_end as timestamp) as encounter_end,
    load_dts,
    record_source
from {{ source('bronze', 'synthea_encounters') }}
