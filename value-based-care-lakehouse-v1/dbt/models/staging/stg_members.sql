-- stg_members.sql
-- Unifies the two member/patient sources into one staging table with a
-- consistent shape. member_bk is the natural/business key in both source
-- systems (DESYNPUF_ID and Synthea Patient.id respectively) - they are
-- disjoint synthetic ID spaces, never overlapping, so a straight UNION ALL
-- is correct here (no matching/merge logic needed).

with synpuf_members as (

    select
        member_bk,
        birth_date,
        sex_code as sex,
        race_code,
        state_code,
        'cms_de_synpuf' as source_system,
        record_source,
        load_dts
    from {{ source('bronze', 'synpuf_beneficiary_summary') }}

),

synthea_members as (

    select
        member_bk,
        birth_date,
        sex,
        cast(null as string) as race_code,
        cast(null as string) as state_code,
        'synthea' as source_system,
        record_source,
        load_dts
    from {{ source('bronze', 'synthea_patients') }}

),

unioned as (

    select * from synpuf_members
    union all
    select * from synthea_members

)

select
    member_bk,
    cast(birth_date as date) as birth_date,
    sex,
    race_code,
    state_code,
    source_system,
    record_source,
    load_dts
from unioned
