-- fact_medication_adherence.sql
-- Per-member, per-drug Proportion of Days Covered (PDC) over a fixed
-- 365-day observation period, from fact_pharmacy_fill. SYNTHETIC fill
-- events on real drug dimensions - see ingestion/pharmacy/README.md.
--
-- SIMPLIFICATION NOTE: true PDC is computed from date-range overlap
-- analysis (deduplicating overlapping fill-coverage windows day by
-- day), which needs a date-spine join this repo doesn't build out. This
-- model instead sums each fill's days_supply, capped at the period
-- length, as a directional approximation - it will overstate PDC for a
-- member with several overlapping/early-refill fills of the same drug.
-- Good enough to demonstrate the metric end-to-end; flagged here rather
-- than presented as a clinically rigorous PDC calculation.

with period as (
    select 365 as period_days
),

fills as (
    select
        member_hk,
        drug_hk,
        sum(days_supply) as raw_days_supply
    from {{ ref('fact_pharmacy_fill') }}
    group by member_hk, drug_hk
)

select
    sha2(concat(f.member_hk, '|', f.drug_hk), 256) as medication_adherence_hk,
    f.member_hk,
    f.drug_hk,
    least(f.raw_days_supply, p.period_days) as days_covered,
    p.period_days,
    least(f.raw_days_supply, p.period_days) / p.period_days as pdc
from fills f
cross join period p
