-- lnk_encounter_facility.sql
-- Links an encounter to the facility it occurred at. Real Synthea data,
-- sourced from the FHIR Encounter.serviceProvider reference added to
-- ingestion/synthea/synthea_schema.py for this domain.

{{
    automate_dv.link(
        src_pk='encounter_facility_hk',
        src_fk=['encounter_hk', 'facility_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounters_hk'
    )
}}
