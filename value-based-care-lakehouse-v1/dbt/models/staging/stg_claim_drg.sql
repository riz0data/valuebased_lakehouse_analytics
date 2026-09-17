-- stg_claim_drg.sql
-- Bridge grain: one row per (claim, DRG) pairing - a claim's DRG
-- assignment is already a column on the claim header, so this is a
-- straight pass-through, not an unpivot.

select
    claim_line_bk,
    drg_bk,
    record_source,
    load_dts
from {{ source('bronze', 'synpuf_inpatient_claim_header') }}
where drg_bk is not null and trim(drg_bk) != ''
