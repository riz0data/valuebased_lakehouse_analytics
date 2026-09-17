-- stg_measures.sql
-- Real CMS Star Ratings measure codes/names (representative subset).
-- Weight values are illustrative, not the official CMS weighting table.
-- See ingestion/clinical_quality/README.md.

select
    measure_bk,
    measure_name,
    measure_weight,
    current_timestamp() as load_dts,
    'cq_measures' as record_source
from {{ source('bronze', 'cq_measures') }}
