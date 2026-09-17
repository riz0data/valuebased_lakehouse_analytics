-- stg_drgs.sql
-- DRG codes, sourced from the real CLM_DRG_CD field already captured in
-- DE-SynPUF Inpatient Claims header (ingestion/de_synpuf), enriched
-- with real CMS MS-DRG relative weights for the DRG codes DE-SynPUF's
-- sample data actually contains (291, 292) plus a couple more for
-- demonstration breadth (293, 470). See
-- ingestion/payment_integrity/reference_data/drg_weights.csv and
-- ingestion/payment_integrity/README.md - this is a small illustrative
-- weight table, not the full CMS IPPS DRG weight file.

with distinct_drgs as (
    select distinct
        drg_bk,
        record_source,
        load_dts
    from {{ source('bronze', 'synpuf_inpatient_claim_header') }}
    where drg_bk is not null and trim(drg_bk) != ''
)

select
    d.drg_bk,
    w.drg_description,
    w.drg_relative_weight,
    d.record_source,
    d.load_dts
from distinct_drgs d
left join {{ source('bronze', 'drg_weights') }} w
    on d.drg_bk = w.drg_bk
