"""
de_synpuf_schema.py

Column definitions for two of the CMS DE-SynPUF file types:

1. Beneficiary Summary File - one row per synthetic beneficiary per year,
   demographics + chronic condition flags + annual cost summaries.
2. Inpatient Claims File - one row per inpatient claim, with diagnosis
   codes spread across 10 wide columns (ICD9_DGNS_CD_1 .. ICD9_DGNS_CD_10)
   and procedure codes across 6 wide columns, which is a real quirk of
   this file format that any ingestion has to handle explicitly.

Source: CMS Data Entrepreneurs' Synthetic Public Use Files (DE-SynPUF)
https://www.cms.gov/data-research/statistics-trends-reports/medicare-claims-synthetic-public-use-files
License: CMS synthetic public use data, free to use.

Note: DE-SynPUF uses ICD-9-CM (it predates the ICD-10 transition), which
is itself public domain, same as ICD-10-CM.
"""

from __future__ import annotations

# ---- Beneficiary Summary File -------------------------------------------------

BENE_SUMMARY_COLUMN_MAP: dict[str, str] = {
    "DESYNPUF_ID": "member_bk",
    "BENE_BIRTH_DT": "birth_date",
    "BENE_DEATH_DT": "death_date",
    "BENE_SEX_IDENT_CD": "sex_code",
    "BENE_RACE_CD": "race_code",
    "BENE_ESRD_IND": "esrd_indicator",
    "SP_STATE_CODE": "state_code",
    "BENE_COUNTY_CD": "county_code",
    "SP_ALZHDMTA": "flag_alzheimers_dementia",
    "SP_CHF": "flag_heart_failure",
    "SP_CHRNKIDN": "flag_chronic_kidney_disease",
    "SP_CNCR": "flag_cancer",
    "SP_COPD": "flag_copd",
    "SP_DEPRESSN": "flag_depression",
    "SP_DIABETES": "flag_diabetes",
    "SP_ISCHMCHT": "flag_ischemic_heart_disease",
    "SP_OSTEOPRS": "flag_osteoporosis",
    "SP_RA_OA": "flag_rheumatoid_osteoarthritis",
    "SP_STRKETIA": "flag_stroke_tia",
    "MEDREIMB_IP": "annual_medicare_reimb_inpatient",
    "MEDREIMB_OP": "annual_medicare_reimb_outpatient",
    "MEDREIMB_CAR": "annual_medicare_reimb_carrier",
}

BENE_SUMMARY_REQUIRED_COLUMNS = list(BENE_SUMMARY_COLUMN_MAP.keys())

# ---- Inpatient Claims File ------------------------------------------------

# Header / one-row-per-claim fields
INPATIENT_HEADER_COLUMN_MAP: dict[str, str] = {
    "DESYNPUF_ID": "member_bk",
    "CLM_ID": "claim_line_bk",
    "CLM_FROM_DT": "service_from_date",
    "CLM_THRU_DT": "service_thru_date",
    "PRVDR_NUM": "provider_bk",
    "CLM_PMT_AMT": "paid_amount",
    "NCH_PRMRY_PYR_CLM_PD_AMT": "primary_payer_paid_amount",
    "CLM_ADMSN_DT": "admission_date",
    "NCH_BENE_DSCHRG_DT": "discharge_date",
    "CLM_DRG_CD": "drg_bk",
    "CLM_UTLZTN_DAY_CNT": "utilization_day_count",
}

INPATIENT_HEADER_REQUIRED_COLUMNS = list(INPATIENT_HEADER_COLUMN_MAP.keys())

# Diagnosis codes are spread across these 10 wide columns in the raw file.
# Ingestion must unpivot them into one normalized row per (claim, diagnosis).
DIAGNOSIS_CODE_COLUMNS = [f"ICD9_DGNS_CD_{i}" for i in range(1, 11)]

# Procedure codes are spread across these 6 wide columns.
PROCEDURE_CODE_COLUMNS = [f"ICD9_PRCDR_CD_{i}" for i in range(1, 7)]

INPATIENT_ALL_RAW_COLUMNS = (
    INPATIENT_HEADER_REQUIRED_COLUMNS + DIAGNOSIS_CODE_COLUMNS + PROCEDURE_CODE_COLUMNS
)
