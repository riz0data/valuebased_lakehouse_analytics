-- stg_encounter_diagnoses.sql
-- Real Synthea condition data, linking each condition (diagnosis) back to
-- the encounter it was recorded on. Diagnosis codes here are SNOMED CT
-- (Synthea's native coding system), unioned at the Hub level with
-- DE-SynPUF's ICD-9 diagnoses per ADR-004-adjacent note in
-- dbt/models/staging/stg_diagnoses.sql - not cross-walked.

select
    encounter_reference as encounter_bk,
    diagnosis_bk,
    diagnosis_description,
    clinical_status_code,
    cast(onset_date as date) as onset_date,
    load_dts,
    record_source
from {{ source('bronze', 'synthea_conditions') }}
where encounter_reference is not null
