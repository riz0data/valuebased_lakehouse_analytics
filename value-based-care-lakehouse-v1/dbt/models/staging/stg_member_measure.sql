-- stg_member_measure.sql
-- SYNTHETIC member-to-measure eligibility assignment. See
-- ingestion/clinical_quality/README.md.

select
    member_bk,
    measure_bk,
    current_timestamp() as load_dts,
    'cq_member_measure' as record_source
from {{ source('bronze', 'cq_member_measure') }}
