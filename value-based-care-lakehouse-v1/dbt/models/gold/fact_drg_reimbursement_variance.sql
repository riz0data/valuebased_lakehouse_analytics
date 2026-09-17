-- fact_drg_reimbursement_variance.sql
-- Per-claim DRG reimbursement variance: actual paid amount vs. an
-- expected amount derived from the DRG's real relative weight and a
-- population-level "dollars per weight unit" benchmark computed from
-- this dataset's own claims (not a real CMS standardized amount).
--
-- SIMPLIFICATION NOTE: a true CMS IPPS expected payment requires the
-- hospital's wage index, labor/non-labor share split, DSH/IME/outlier
-- adjustments, and the fiscal year's national standardized amount -
-- none of which is available per-facility in this repo's data (see
-- ingestion/payment_integrity/README.md on the DRG weight reference
-- table). Rather than fabricate a fake standardized-amount constant,
-- this model benchmarks each claim against the average paid-amount-per-
-- unit-of-relative-weight across all DRG-coded claims in the dataset,
-- so "expected" reflects this population's own reimbursement pattern.
-- Directionally useful for spotting outliers; not a substitute for a
-- real IPPS payment calculator.

with claims_with_weight as (
    select
        f.payment_txn_hk,
        f.claim_line_hk,
        f.provider_hk,
        f.drg_hk,
        f.paid_amount,
        d.drg_relative_weight
    from {{ ref('fact_claim_payment') }} f
    left join {{ ref('dim_drg') }} d
        on f.drg_hk = d.drg_hk
    where d.drg_relative_weight is not null
),

benchmark as (
    select
        sum(paid_amount) / nullif(sum(drg_relative_weight), 0) as dollars_per_weight_unit
    from claims_with_weight
)

select
    c.payment_txn_hk,
    c.claim_line_hk,
    c.provider_hk,
    c.drg_hk,
    c.drg_relative_weight,
    c.paid_amount,
    b.dollars_per_weight_unit,
    (c.drg_relative_weight * b.dollars_per_weight_unit) as expected_paid_amount,
    c.paid_amount - (c.drg_relative_weight * b.dollars_per_weight_unit) as reimbursement_variance
from claims_with_weight c
cross join benchmark b
