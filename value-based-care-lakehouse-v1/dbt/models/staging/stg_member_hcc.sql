-- stg_member_hcc.sql
-- SYNTHETIC member-to-HCC assignment, now including the coding-gap
-- lifecycle fields (active_flag, coding_gap_identified_date,
-- coding_gap_closed_date) that feed sat_member_hcc_status and Coding
-- Gap Closure Rate. See ingestion/risk_adjustment/README.md.

select
    member_bk,
    hcc_bk,
    active_flag,
    cast(coding_gap_identified_date as date) as coding_gap_identified_date,
    cast(nullif(coding_gap_closed_date, '') as date) as coding_gap_closed_date,
    current_timestamp() as load_dts,
    'ra_member_hcc' as record_source
from {{ source('bronze', 'ra_member_hcc') }}
