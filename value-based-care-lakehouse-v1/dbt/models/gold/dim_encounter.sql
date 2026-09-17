-- dim_encounter.sql
-- Encounter dimension, built from hub_encounter + sat_encounter_details.
-- Real Synthea data. Now includes encounter_end for Readmission Rate.

select
    h.encounter_hk,
    h.encounter_bk as encounter_id,
    s.encounter_class_code,
    s.encounter_start,
    s.encounter_end
from {{ ref('hub_encounter') }} h
left join {{ ref('sat_encounter_details') }} s
    on h.encounter_hk = s.encounter_hk
