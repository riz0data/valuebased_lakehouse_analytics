-- fact_hcc_capture.sql
-- Per-member, per-HCC comparison of suspected vs. captured/coded status
-- - feeds HCC Capture Rate and Suspecting Yield Rate. Built as a full
-- outer union of lnk_member_suspected_hcc and lnk_member_hcc so a
-- member-HCC pair that's suspected-but-not-captured, captured-but-not-
-- suspected (e.g. coded from a source outside the suspecting engine's
-- reach), or both, is represented correctly. SYNTHETIC - see
-- ingestion/risk_adjustment/README.md.

with suspected as (
    select member_hk, hcc_hk, 1 as is_suspected
    from {{ ref('lnk_member_suspected_hcc') }}
),

captured as (
    select member_hk, hcc_hk, 1 as is_captured
    from {{ ref('lnk_member_hcc') }}
),

combined as (
    select coalesce(s.member_hk, c.member_hk) as member_hk,
           coalesce(s.hcc_hk, c.hcc_hk) as hcc_hk,
           coalesce(s.is_suspected, 0) as is_suspected,
           coalesce(c.is_captured, 0) as is_captured
    from suspected s
    full outer join captured c
        on s.member_hk = c.member_hk and s.hcc_hk = c.hcc_hk
)

select
    sha2(concat(member_hk, '|', hcc_hk), 256) as hcc_capture_hk,
    member_hk,
    hcc_hk,
    is_suspected,
    is_captured,
    case when is_suspected = 1 and is_captured = 1 then 1 else 0 end as is_captured_and_suspected
from combined
