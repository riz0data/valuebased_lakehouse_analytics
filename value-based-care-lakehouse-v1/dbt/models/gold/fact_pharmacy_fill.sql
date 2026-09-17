-- fact_pharmacy_fill.sql
-- Prescription fill fact at the fill-event grain, enriched with the
-- drug's NDC for Medication Adherence (PDC) calculations. SYNTHETIC
-- fill events on real drug/pharmacy dimensions - see
-- ingestion/pharmacy/README.md.

select
    t.pharmacy_fill_txn_hk,
    t.member_hk,
    t.drug_hk,
    d.ndc,
    t.pharmacy_hk,
    t.fill_date,
    t.days_supply,
    t.effective_from
from {{ ref('tlnk_pharmacy_fill_txn') }} t
left join {{ ref('dim_drug') }} d
    on t.drug_hk = d.drug_hk
