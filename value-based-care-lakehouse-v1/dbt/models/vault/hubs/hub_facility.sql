-- hub_facility.sql
-- Hub for organizations/facilities, keyed on organizational NPI (NPPES).

{{
    automate_dv.hub(
        src_pk='facility_hk',
        src_nk='facility_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_facilities_hk'
    )
}}
