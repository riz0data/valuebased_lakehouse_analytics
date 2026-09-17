"""
Generates small sample CSVs in the exact DE-SynPUF column format (fabricated
IDs and values, not real CMS data) so land_de_synpuf.py can be tested
end-to-end without needing to download the real files from CMS.

TEST FIXTURE ONLY - not part of the shipped ingestion pipeline.
"""
import csv

BENE_HEADER = [
    "DESYNPUF_ID", "BENE_BIRTH_DT", "BENE_DEATH_DT", "BENE_SEX_IDENT_CD",
    "BENE_RACE_CD", "BENE_ESRD_IND", "SP_STATE_CODE", "BENE_COUNTY_CD",
    "SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
    "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS", "SP_RA_OA",
    "SP_STRKETIA", "MEDREIMB_IP", "MEDREIMB_OP", "MEDREIMB_CAR",
]

BENE_ROWS = [
    ["00013D2EFD8E45D1", "19230501", "", "1", "1", "0", "39", "230",
     "1", "2", "2", "2", "2", "2", "1", "2", "2", "2", "2", "1200", "300", "150"],
    ["00016F745862898F", "19430101", "", "2", "1", "0", "39", "230",
     "2", "1", "2", "2", "2", "2", "2", "1", "2", "1", "2", "0", "500", "220"],
    # duplicate DESYNPUF_ID to exercise de-dupe
    ["00013D2EFD8E45D1", "19230501", "", "1", "1", "0", "39", "230",
     "1", "2", "2", "2", "2", "2", "1", "2", "2", "2", "2", "1400", "310", "160"],
]

INPATIENT_HEADER = (
    ["DESYNPUF_ID", "CLM_ID", "CLM_FROM_DT", "CLM_THRU_DT", "PRVDR_NUM",
     "CLM_PMT_AMT", "NCH_PRMRY_PYR_CLM_PD_AMT", "CLM_ADMSN_DT",
     "NCH_BENE_DSCHRG_DT", "CLM_DRG_CD", "CLM_UTLZTN_DAY_CNT"]
    + [f"ICD9_DGNS_CD_{i}" for i in range(1, 11)]
    + [f"ICD9_PRCDR_CD_{i}" for i in range(1, 7)]
)

INPATIENT_ROWS = [
    # claim with 3 diagnosis codes and 1 procedure code, rest blank
    ["00013D2EFD8E45D1", "196201039265290", "20100112", "20100115", "390001",
     "5400.00", "0.00", "20100112", "20100115", "291", "3",
     "41401", "4280", "2720", "", "", "", "", "", "", "",
     "3615", "", "", "", "", ""],
    # claim with only 1 diagnosis code
    ["00016F745862898F", "196242039265999", "20100203", "20100206", "390002",
     "3200.00", "0.00", "20100203", "20100206", "292", "3",
     "5849", "", "", "", "", "", "", "", "", "",
     "", "", "", "", "", ""],
]

with open("/home/claude/synpuf_work/sample_bene_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(BENE_HEADER)
    w.writerows(BENE_ROWS)

with open("/home/claude/synpuf_work/sample_inpatient_claims.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(INPATIENT_HEADER)
    w.writerows(INPATIENT_ROWS)

print("Sample DE-SynPUF files written.")
