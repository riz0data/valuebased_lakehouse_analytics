-- fact_risk_score_accuracy.sql
-- Per-member comparison of the member's actual (coded) RAF score
-- against a "clinically suspected" RAF approximation - sum of the HCC
-- weights for that member's suspected-but-possibly-uncoded HCCs (from
-- fact_hcc_capture) - feeds Risk Score Accuracy.
--
-- SIMPLIFICATION NOTE: a real CMS-HCC RAF score is not simply the sum
-- of HCC weights - it also includes demographic factors, interaction
-- terms between HCCs, and disease-hierarchy logic (some HCCs "trump"
-- others), which this repo's synthetic weight table doesn't model. This
-- suspected-RAF approximation is a directional signal for "does this
-- member look meaningfully under-coded", not a substitute for a real
-- CMS-HCC risk score calculator. SYNTHETIC underlying data - see
-- ingestion/risk_adjustment/README.md.

with suspected_weight as (
    select
        fc.member_hk,
        sum(dh.hcc_weight) as suspected_raf_approx
    from {{ ref('fact_hcc_capture') }} fc
    left join {{ ref('dim_hcc_category') }} dh
        on fc.hcc_hk = dh.hcc_hk
    where fc.is_suspected = 1
    group by fc.member_hk
),

actual_raf as (
    select
        member_hk,
        risk_model_hk,
        raf_score,
        model_year
    from {{ ref('fact_member_risk_score') }}
)

select
    a.member_hk,
    a.risk_model_hk,
    a.model_year,
    a.raf_score as actual_raf_score,
    sw.suspected_raf_approx,
    a.raf_score - coalesce(sw.suspected_raf_approx, 0) as raf_accuracy_variance
from actual_raf a
left join suspected_weight sw
    on a.member_hk = sw.member_hk
