"""
land_de_synpuf.py

Lands two CMS DE-SynPUF file types into the Bronze layer:

1. Beneficiary Summary File -> one clean row per member per year
   (demographics, chronic condition flags, annual cost summaries).
2. Inpatient Claims File -> split into two normalized outputs:
     - claim header (one row per claim)
     - claim diagnoses (one row per claim x diagnosis code, unpivoted
       from the 10 wide ICD9_DGNS_CD_1..10 columns in the raw file)
   This unpivot step is the main real-world wrinkle in this file format -
   diagnosis and procedure codes are NOT normalized in the source, and
   flattening them is required before they can feed hub_diagnosis /
   lnk_claim_diagnosis in the Vault layer.

Like land_nppes.py, this runs on pandas locally/for testing and has a
PySpark equivalent for production use inside a Databricks job.

Usage:
    python land_de_synpuf.py --bene-input DE1_0_2010_Beneficiary_Summary.csv \\
        --inpatient-input DE1_0_2010_Inpatient_Claims.csv \\
        --output-dir ./bronze/de_synpuf

Source: https://www.cms.gov/data-research/statistics-trends-reports/medicare-claims-synthetic-public-use-files
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

import pandas as pd

from de_synpuf_schema import (
    BENE_SUMMARY_COLUMN_MAP,
    BENE_SUMMARY_REQUIRED_COLUMNS,
    DIAGNOSIS_CODE_COLUMNS,
    INPATIENT_ALL_RAW_COLUMNS,
    INPATIENT_HEADER_COLUMN_MAP,
    INPATIENT_HEADER_REQUIRED_COLUMNS,
    PROCEDURE_CODE_COLUMNS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("land_de_synpuf")

RECORD_SOURCE = "cms_de_synpuf"
CHUNK_SIZE = 50_000


def _bronze_meta(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["record_source"] = RECORD_SOURCE
    df["load_dts"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return df


def _write(df: pd.DataFrame, path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "parquet":
        try:
            df.to_parquet(path.with_suffix(".parquet"), index=False)
            return
        except ImportError:
            logger.warning("No Parquet engine installed - falling back to CSV for %s", path.name)
    df.to_csv(path.with_suffix(".csv"), index=False)


def _require_columns(df: pd.DataFrame, required: list[str], file_label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{file_label} is missing expected DE-SynPUF columns: {missing}. "
            "Check that this is a genuine DE-SynPUF file and the header wasn't altered."
        )


# ---- Beneficiary Summary ---------------------------------------------------

def land_beneficiary_summary(input_path: str, output_dir: str, fmt: str = "parquet") -> dict:
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Beneficiary Summary file not found: {input_path}")

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    _require_columns(df, BENE_SUMMARY_REQUIRED_COLUMNS, "Beneficiary Summary file")

    selected = df[BENE_SUMMARY_REQUIRED_COLUMNS].rename(columns=BENE_SUMMARY_COLUMN_MAP)
    selected = selected.drop_duplicates(subset=["member_bk"], keep="last")
    selected = _bronze_meta(selected)

    _write(selected, Path(output_dir) / "beneficiary_summary", fmt)

    summary = {"input_rows": len(df), "members_landed": len(selected)}
    logger.info("Beneficiary Summary: %s", summary)
    return summary


# ---- Inpatient Claims -------------------------------------------------------

def _unpivot_codes(df: pd.DataFrame, code_columns: list[str], value_name: str) -> pd.DataFrame:
    """
    Turns N wide code columns (e.g. ICD9_DGNS_CD_1..10) into a long/tidy
    table: one row per (claim_line_bk, code), dropping empty/NaN codes.
    """
    long_df = df.melt(
        id_vars=["claim_line_bk"],
        value_vars=[c for c in code_columns if c in df.columns],
        value_name=value_name,
    )
    long_df = long_df.dropna(subset=[value_name])
    long_df = long_df[long_df[value_name].astype(str).str.strip() != ""]
    return long_df[["claim_line_bk", value_name]].reset_index(drop=True)


def process_inpatient_chunk(chunk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (claim_header, claim_diagnoses, claim_procedures) for one chunk."""
    _require_columns(chunk, INPATIENT_HEADER_REQUIRED_COLUMNS, "Inpatient Claims file")

    header = chunk[INPATIENT_HEADER_REQUIRED_COLUMNS].rename(columns=INPATIENT_HEADER_COLUMN_MAP)

    # melt() needs claim_line_bk under its raw name to key off of, so build
    # a small working frame with the raw CLM_ID column preserved for the join key.
    working = chunk.rename(columns={"CLM_ID": "claim_line_bk"})
    diagnoses = _unpivot_codes(working, DIAGNOSIS_CODE_COLUMNS, "diagnosis_bk")
    procedures = _unpivot_codes(working, PROCEDURE_CODE_COLUMNS, "procedure_bk")

    return header, diagnoses, procedures


def land_inpatient_claims(input_path: str, output_dir: str, fmt: str = "parquet") -> dict:
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Inpatient Claims file not found: {input_path}")

    header_chunks, dgns_chunks, prcdr_chunks = [], [], []
    total_rows = 0

    reader = pd.read_csv(
        input_file,
        chunksize=CHUNK_SIZE,
        dtype=str,
        low_memory=False,
        usecols=lambda c: c in INPATIENT_ALL_RAW_COLUMNS,
    )

    for i, chunk in enumerate(reader):
        total_rows += len(chunk)
        header, dgns, prcdr = process_inpatient_chunk(chunk)
        header_chunks.append(header)
        dgns_chunks.append(dgns)
        prcdr_chunks.append(prcdr)
        logger.info(
            "Inpatient chunk %s: %s claims -> %s diagnosis rows, %s procedure rows",
            i, len(chunk), len(dgns), len(prcdr),
        )

    header_df = pd.concat(header_chunks, ignore_index=True).drop_duplicates(subset=["claim_line_bk"])
    dgns_df = pd.concat(dgns_chunks, ignore_index=True).drop_duplicates()
    prcdr_df = pd.concat(prcdr_chunks, ignore_index=True).drop_duplicates()

    header_df = _bronze_meta(header_df)
    dgns_df = _bronze_meta(dgns_df)
    prcdr_df = _bronze_meta(prcdr_df)

    out = Path(output_dir)
    _write(header_df, out / "inpatient_claim_header", fmt)
    _write(dgns_df, out / "inpatient_claim_diagnoses", fmt)
    _write(prcdr_df, out / "inpatient_claim_procedures", fmt)

    summary = {
        "input_rows": total_rows,
        "claims_landed": len(header_df),
        "diagnosis_rows_landed": len(dgns_df),
        "procedure_rows_landed": len(prcdr_df),
    }
    logger.info("Inpatient Claims: %s", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Land CMS DE-SynPUF files into Bronze.")
    parser.add_argument("--bene-input", help="Path to the Beneficiary Summary CSV.")
    parser.add_argument("--inpatient-input", help="Path to the Inpatient Claims CSV.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    args = parser.parse_args()

    if not args.bene_input and not args.inpatient_input:
        parser.error("Provide at least one of --bene-input or --inpatient-input")

    if args.bene_input:
        land_beneficiary_summary(args.bene_input, args.output_dir, args.format)
    if args.inpatient_input:
        land_inpatient_claims(args.inpatient_input, args.output_dir, args.format)


if __name__ == "__main__":
    sys.exit(main())
