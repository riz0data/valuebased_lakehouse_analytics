-- fact_readmission.sql
-- 30-day all-cause readmission fact: for each inpatient (class code
-- IMP) encounter, flags whether the same member had another inpatient
-- encounter starting within 30 days after this one's discharge
-- (encounter_end) - feeds Readmission Rate. Real Synthea data (IMP
-- encounter class is a real FHIR R4 Encounter.class code -
-- hl7.org/fhir/R4/v3/ActEncounterCode/vs.html).
--
-- SIMPLIFICATION NOTE: a real CMS 30-day readmission measure excludes
-- planned readmissions, applies condition-specific cohort logic, and
-- handles transfers/same-day readmissions with additional rules. This
-- model is the general all-cause version: any inpatient encounter
-- followed by another inpatient encounter for the same member within 30
-- days counts as a readmission, with no exclusions applied.

with inpatient_encounters as (
    select
        encounter_hk,
        member_hk,
        encounter_start,
        encounter_end
    from {{ ref('fact_encounter') }}
    where encounter_class_code = 'IMP'
      and member_hk is not null
),

with_next_admission as (
    select
        i.encounter_hk as index_encounter_hk,
        i.member_hk,
        i.encounter_start as index_admission_date,
        i.encounter_end as index_discharge_date,
        min(case
            when n.encounter_start > i.encounter_end
             and n.encounter_start <= dateadd(day, 30, i.encounter_end)
            then n.encounter_start
        end) as next_admission_within_30_days
    from inpatient_encounters i
    left join inpatient_encounters n
        on i.member_hk = n.member_hk
       and n.encounter_hk != i.encounter_hk
    group by i.encounter_hk, i.member_hk, i.encounter_start, i.encounter_end
)

select
    index_encounter_hk,
    member_hk,
    index_admission_date,
    index_discharge_date,
    next_admission_within_30_days,
    case when next_admission_within_30_days is not null then 1 else 0 end as is_readmission
from with_next_admission
where index_discharge_date is not null
