-- dim_hcc_category.sql
-- HCC category dimension, built from hub_hcc_category + sat_hcc_category_details.
-- Real category codes/descriptions; weights illustrative - see
-- ingestion/risk_adjustment/README.md.

select
    h.hcc_hk,
    h.hcc_bk as hcc_code,
    s.hcc_description,
    s.hcc_weight
from {{ ref('hub_hcc_category') }} h
left join {{ ref('sat_hcc_category_details') }} s
    on h.hcc_hk = s.hcc_hk
