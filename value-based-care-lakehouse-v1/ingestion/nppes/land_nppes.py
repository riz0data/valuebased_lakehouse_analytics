"""
land_nppes.py

Lands the public NPPES NPI Registry bulk file into the Bronze layer.

This script is written to run in two modes:

1. Local / test mode (default, no Spark required):
   Reads the NPPES CSV (or a local sample of it) in chunks with pandas,
   selects and renames the columns defined in nppes_schema.py, splits
   records into providers (Entity Type 1) and organizations/facilities
   (Entity Type 2), and writes them out as Parquet (or CSV if a Parquet
   engine isn't installed) with Bronze metadata columns attached.

2. Databricks mode (--engine spark):
   Uses PySpark + Auto Loader-style batch read instead of pandas, for
   running inside an actual Databricks job. The transformation logic is
   identical; only the I/O layer changes. This path requires `pyspark`
   to be installed and is not exercised by the local test suite.

Usage:
    # Land a real NPPES bulk file (~9 GB, one file per month from CMS)
    python land_nppes.py --input /path/to/npidata_pfile_20260101.csv \\
        --output-dir ./bronze/nppes

    # Run against a small sample for local testing
    python land_nppes.py --input sample_nppes.csv --output-dir ./bronze/nppes --format csv

Source: https://download.cms.gov/nppes/NPI_Files.html (public domain)
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

import pandas as pd

from nppes_schema import (
    ENTITY_TYPE_INDIVIDUAL,
    ENTITY_TYPE_ORGANIZATION,
    NPPES_COLUMN_MAP,
    REQUIRED_SOURCE_COLUMNS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("land_nppes")

RECORD_SOURCE = "nppes_npi_registry"
CHUNK_SIZE = 100_000


def _add_bronze_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Attach standard Bronze-layer lineage columns."""
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
            logger.warning(
                "No Parquet engine (pyarrow/fastparquet) installed - "
                "falling back to CSV for %s", path.name
            )
    df.to_csv(path.with_suffix(".csv"), index=False)


def land_de_dupe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact-duplicate NPI rows, keeping the most recently updated."""
    if "last_update_date" in df.columns:
        df = df.sort_values("last_update_date")
    return df.drop_duplicates(subset=["npi"], keep="last")


def process_chunk(chunk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Select/rename columns per nppes_schema, then split into
    provider (individual) and facility (organization) records.
    """
    missing = [c for c in REQUIRED_SOURCE_COLUMNS if c not in chunk.columns]
    if missing:
        raise ValueError(
            f"Input file is missing expected NPPES columns: {missing}. "
            "Check that this is a genuine NPPES bulk file and that the "
            "header row wasn't altered."
        )

    selected = chunk[REQUIRED_SOURCE_COLUMNS].rename(columns=NPPES_COLUMN_MAP)

    providers = selected[selected["entity_type_code"] == ENTITY_TYPE_INDIVIDUAL]
    facilities = selected[selected["entity_type_code"] == ENTITY_TYPE_ORGANIZATION]

    return providers.copy(), facilities.copy()


def land_nppes(input_path: str, output_dir: str, fmt: str = "parquet") -> dict:
    """
    Main entry point. Reads the NPPES bulk file in chunks (it's too large
    to load into memory at once - the real file is several GB) and lands
    provider and facility records separately.

    Returns a summary dict for logging / CI assertions.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"NPPES input file not found: {input_path}")

    out_dir = Path(output_dir)
    provider_chunks: list[pd.DataFrame] = []
    facility_chunks: list[pd.DataFrame] = []

    logger.info("Reading NPPES file in chunks of %s rows: %s", CHUNK_SIZE, input_path)

    reader = pd.read_csv(
        input_file,
        chunksize=CHUNK_SIZE,
        dtype=str,          # NPPES fields (NPI, ZIP, etc.) must not be coerced to numeric
        low_memory=False,
    )

    total_rows = 0
    for i, chunk in enumerate(reader):
        total_rows += len(chunk)
        providers, facilities = process_chunk(chunk)
        provider_chunks.append(providers)
        facility_chunks.append(facilities)
        logger.info(
            "Chunk %s: %s rows -> %s providers, %s facilities",
            i, len(chunk), len(providers), len(facilities),
        )

    providers_df = land_de_dupe(pd.concat(provider_chunks, ignore_index=True))
    facilities_df = land_de_dupe(pd.concat(facility_chunks, ignore_index=True))

    providers_df = _add_bronze_metadata(providers_df)
    facilities_df = _add_bronze_metadata(facilities_df)

    _write(providers_df, out_dir / "providers", fmt)
    _write(facilities_df, out_dir / "facilities", fmt)

    summary = {
        "input_rows": total_rows,
        "providers_landed": len(providers_df),
        "facilities_landed": len(facilities_df),
        "output_dir": str(out_dir),
    }
    logger.info("Done: %s", summary)
    return summary


def land_nppes_spark(input_path: str, output_dir: str):  # pragma: no cover
    """
    Databricks/Spark equivalent of land_nppes(), for production use inside
    a Databricks job. Not exercised locally - requires a Spark session.
    """
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = SparkSession.builder.getOrCreate()

    raw = spark.read.option("header", True).csv(input_path)
    missing = [c for c in REQUIRED_SOURCE_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Input file is missing expected NPPES columns: {missing}")

    selected = raw.select(*REQUIRED_SOURCE_COLUMNS)
    for src, dest in NPPES_COLUMN_MAP.items():
        selected = selected.withColumnRenamed(src, dest)

    selected = selected.withColumn("record_source", F.lit(RECORD_SOURCE)) \
                        .withColumn("load_dts", F.current_timestamp())

    providers = selected.filter(F.col("entity_type_code") == ENTITY_TYPE_INDIVIDUAL)
    facilities = selected.filter(F.col("entity_type_code") == ENTITY_TYPE_ORGANIZATION)

    providers.dropDuplicates(["npi"]).write.mode("overwrite").format("delta") \
        .save(f"{output_dir}/providers")
    facilities.dropDuplicates(["npi"]).write.mode("overwrite").format("delta") \
        .save(f"{output_dir}/facilities")


def main():
    parser = argparse.ArgumentParser(description="Land the NPPES NPI Registry bulk file into Bronze.")
    parser.add_argument("--input", required=True, help="Path to the NPPES bulk CSV file.")
    parser.add_argument("--output-dir", required=True, help="Directory to write Bronze output into.")
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("--engine", choices=["pandas", "spark"], default="pandas")
    args = parser.parse_args()

    if args.engine == "spark":
        land_nppes_spark(args.input, args.output_dir)
    else:
        land_nppes(args.input, args.output_dir, args.format)


if __name__ == "__main__":
    sys.exit(main())
