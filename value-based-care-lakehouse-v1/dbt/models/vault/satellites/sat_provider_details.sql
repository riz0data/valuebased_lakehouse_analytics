-- sat_provider_details.sql
-- Tracks provider descriptive attributes (name, credential, specialty
-- taxonomy, practice location) over time.

{{
    automate_dv.sat(
        src_pk='provider_hk',
        src_hashdiff='provider_hashdiff',
        src_payload=['provider_first_name', 'provider_last_name', 'provider_credential',
                     'primary_taxonomy_code', 'practice_state', 'practice_city'],
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_providers_sat_hk'
    )
}}
