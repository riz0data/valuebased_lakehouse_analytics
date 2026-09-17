-- stg_drugs.sql
-- Drugs, from the real FDA NDC Directory (product.txt). drug_bk is the
-- real NDC (PRODUCTNDC). drug_name prefers the brand name
-- (PROPRIETARYNAME) and falls back to the generic name
-- (NONPROPRIETARYNAME) when no brand name is listed. See
-- ingestion/pharmacy/README.md.

select
    productndc as drug_bk,
    coalesce(nullif(proprietaryname, ''), nonproprietaryname) as drug_name,
    pharm_classes as drug_class,
    record_source,
    load_dts
from {{ source('bronze', 'ndc_products') }}
