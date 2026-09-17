-- dim_drug.sql
-- Drug dimension, built from hub_drug + sat_drug_details. Real FDA NDC
-- Directory data.

select
    h.drug_hk,
    h.drug_bk as ndc,
    s.drug_name,
    s.drug_class
from {{ ref('hub_drug') }} h
left join {{ ref('sat_drug_details') }} s
    on h.drug_hk = s.drug_hk
