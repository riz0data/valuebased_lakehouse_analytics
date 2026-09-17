-- fact_encounter.sql
-- Encounter fact at the encounter grain, enriched with member/provider/
-- facility keys - feeds ED Utilization Rate and Readmission Rate. Real
-- Synthea data.

select
    e.encounter_hk,
    lme.member_hk,
    lep.provider_hk,
    lef.facility_hk,
    e.encounter_class_code,
    e.encounter_start,
    e.encounter_end
from {{ ref('dim_encounter') }} e
left join {{ ref('lnk_member_encounter') }} lme
    on e.encounter_hk = lme.encounter_hk
left join {{ ref('lnk_encounter_provider') }} lep
    on e.encounter_hk = lep.encounter_hk
left join {{ ref('lnk_encounter_facility') }} lef
    on e.encounter_hk = lef.encounter_hk
