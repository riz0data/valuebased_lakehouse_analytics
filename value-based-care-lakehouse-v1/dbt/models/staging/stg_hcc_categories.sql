-- stg_hcc_categories.sql
-- Real CMS-HCC V28 category codes/descriptions (representative subset).
-- hcc_weight values are illustrative, not the official CMS relative
-- factor table. See ingestion/risk_adjustment/README.md.

select
    hcc_bk,
    hcc_description,
    hcc_weight,
    current_timestamp() as load_dts,
    'ra_hcc_categories' as record_source
from {{ source('bronze', 'ra_hcc_categories') }}
