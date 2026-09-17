-- stg_suspected_hcc.sql
-- SYNTHETIC suspected HCC fixture - what a clinical-evidence suspecting
-- engine would flag as a plausible-but-not-yet-coded HCC for a member.
-- Deliberately a separate fabricated fixture from stg_member_hcc's
-- captured/coded HCCs - see
-- ingestion/risk_adjustment/make_risk_adjustment_sample.py
-- (make_suspected_hcc) for why this can't be derived from this repo's
-- real diagnosis data (ICD-10-CM-only CMS-HCC crosswalk vs. this repo's
-- ICD-9-CM/SNOMED diagnosis data - see ADR-004 in
-- docs/decisions/ADRs.md).

select
    member_bk,
    hcc_bk,
    current_timestamp() as load_dts,
    'ra_suspected_hcc' as record_source
from {{ source('bronze', 'ra_suspected_hcc') }}
