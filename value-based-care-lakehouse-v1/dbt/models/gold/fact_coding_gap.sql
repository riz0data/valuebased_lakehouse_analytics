-- fact_coding_gap.sql
-- Per-member-HCC coding-gap lifecycle fact, from sat_member_hcc_status -
-- feeds Coding Gap Closure Rate. SYNTHETIC - see
-- ingestion/risk_adjustment/README.md.

select
    l.member_hcc_hk,
    l.member_hk,
    l.hcc_hk,
    s.active_flag,
    s.coding_gap_identified_date,
    s.coding_gap_closed_date,
    case when s.coding_gap_closed_date is not null then 1 else 0 end as is_gap_closed
from {{ ref('lnk_member_hcc') }} l
left join {{ ref('sat_member_hcc_status') }} s
    on l.member_hcc_hk = s.member_hcc_hk
