-- dim_measure.sql
-- Quality measure dimension, built from hub_measure + sat_measure_definition.
-- Real CMS Star Ratings measure codes/names; illustrative weights - see
-- ingestion/clinical_quality/README.md.

select
    h.measure_hk,
    h.measure_bk as measure_code,
    s.measure_name,
    s.measure_weight
from {{ ref('hub_measure') }} h
left join {{ ref('sat_measure_definition') }} s
    on h.measure_hk = s.measure_hk
