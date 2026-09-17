-- dim_drg.sql
-- DRG dimension, built from hub_drg + sat_drg_details. drg_bk is the
-- real CLM_DRG_CD field from DE-SynPUF; drg_description and
-- drg_relative_weight come from the real (illustrative-subset) CMS
-- MS-DRG weight reference table - see
-- ingestion/payment_integrity/reference_data/drg_weights.csv and
-- ingestion/payment_integrity/README.md.

select
    h.drg_hk,
    h.drg_bk,
    s.drg_description,
    s.drg_relative_weight
from {{ ref('hub_drg') }} h
left join {{ ref('sat_drg_details') }} s
    on h.drg_hk = s.drg_hk
