-- dim_procedure.sql
-- Procedure dimension, built from hub_procedure + sat_procedure_details.
-- NOTE: sourced from DE-SynPUF ICD-9 procedure codes, not HCPCS Level II
-- - see ingestion/payment_integrity/README.md and ADR-004's amendment.

select
    h.procedure_hk,
    h.procedure_bk as procedure_code,
    s.coding_system
from {{ ref('hub_procedure') }} h
left join {{ ref('sat_procedure_details') }} s
    on h.procedure_hk = s.procedure_hk
