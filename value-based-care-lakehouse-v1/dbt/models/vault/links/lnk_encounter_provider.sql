-- lnk_encounter_provider.sql
-- Links an encounter to its attending provider. Real Synthea data,
-- sourced from the FHIR Encounter.participant.individual reference
-- added to ingestion/synthea/synthea_schema.py for this domain.

{{
    automate_dv.link(
        src_pk='encounter_provider_hk',
        src_fk=['encounter_hk', 'provider_hk'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_encounters_hk'
    )
}}
