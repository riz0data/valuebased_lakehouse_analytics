"""
land_synthea.py

Lands MITRE Synthea synthetic patient FHIR Bundles into the Bronze layer.

Unlike the CSV-based CMS sources (DE-SynPUF, NPPES), Synthea's canonical
output is one FHIR R4 Bundle (JSON) per patient, with each bundle
containing a mix of resource types (Patient, Encounter, Condition, etc.)
as bundle.entry[].resource objects. This script:

  1. Reads every *.json bundle file in an input directory.
  2. Walks each bundle's entries and buckets resources by resourceType.
  3. Flattens each supported resource type into a tabular row using the
     field-path maps in synthea_schema.py (dot-notation into nested JSON,
     including array indexing like "type.0.text").
  4. Writes one Bronze output table per resource type (patients,
     encounters, conditions).

Usage:
    python land_synthea.py --input-dir ./synthea_output/fhir --output-dir ./bronze/synthea

Source: https://github.com/synthetichealth/synthea (Apache License 2.0)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from synthea_schema import (
    CONDITION_FIELDS,
    ENCOUNTER_FIELDS,
    PATIENT_FIELDS,
    SUPPORTED_RESOURCE_TYPES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("land_synthea")

RECORD_SOURCE = "synthea_fhir_bundle"

FIELD_MAPS = {
    "Patient": PATIENT_FIELDS,
    "Encounter": ENCOUNTER_FIELDS,
    "Condition": CONDITION_FIELDS,
}


def _get_path(obj: dict, path: str) -> Any:
    """
    Resolves a dot-notation path into nested JSON, with numeric segments
    treated as list indices. E.g. "type.0.text" on
    {"type": [{"text": "well child visit"}]} -> "well child visit".
    Returns None if any segment is missing, rather than raising - FHIR
    resources are optional-field-heavy by design, and a missing field is
    normal, not an error.
    """
    current = obj
    for segment in path.split("."):
        if current is None:
            return None
        if segment.isdigit():
            idx = int(segment)
            if not isinstance(current, list) or idx >= len(current):
                return None
            current = current[idx]
        else:
            if not isinstance(current, dict) or segment not in current:
                return None
            current = current[segment]
    return current


def flatten_resource(resource: dict, field_map: dict[str, str]) -> dict:
    return {dest: _get_path(resource, src) for src, dest in field_map.items()}


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


def parse_bundle(bundle: dict) -> dict[str, list[dict]]:
    """
    Walks one FHIR Bundle's entries and returns flattened rows grouped
    by resource type, for every resourceType in SUPPORTED_RESOURCE_TYPES.
    Unsupported resource types present in the bundle are silently skipped.
    """
    buckets: dict[str, list[dict]] = {rt: [] for rt in SUPPORTED_RESOURCE_TYPES}

    entries = bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")
        if rtype in FIELD_MAPS:
            buckets[rtype].append(flatten_resource(resource, FIELD_MAPS[rtype]))

    return buckets


def _clean_reference(ref) -> str | None:
    """FHIR references look like 'urn:uuid:<id>' or 'Patient/<id>' - strip to the bare id.
    Missing references arrive as None or, once round-tripped through a pandas
    DataFrame column, as float NaN - both must be treated as "no reference"."""
    if ref is None or (isinstance(ref, float)):
        return None
    if not ref:
        return ref
    return str(ref).split(":")[-1].split("/")[-1]


def land_synthea(input_dir: str, output_dir: str, fmt: str = "parquet") -> dict:
    in_dir = Path(input_dir)
    if not in_dir.exists():
        raise FileNotFoundError(f"Synthea input directory not found: {input_dir}")

    bundle_files = sorted(in_dir.glob("*.json"))
    if not bundle_files:
        raise ValueError(f"No .json bundle files found in {input_dir}")

    all_rows: dict[str, list[dict]] = {rt: [] for rt in SUPPORTED_RESOURCE_TYPES}

    for bundle_file in bundle_files:
        with open(bundle_file) as f:
            bundle = json.load(f)
        buckets = parse_bundle(bundle)
        for rtype, rows in buckets.items():
            all_rows[rtype].extend(rows)

    logger.info("Parsed %s bundle files", len(bundle_files))

    frames = {}
    for rtype in SUPPORTED_RESOURCE_TYPES:
        df = pd.DataFrame(all_rows[rtype])
        if not df.empty:
            for col in ("member_reference", "encounter_reference", "provider_reference", "facility_reference"):
                if col in df.columns:
                    df[col] = df[col].apply(_clean_reference)
        frames[rtype] = _bronze_meta(df)

    out = Path(output_dir)
    output_names = {"Patient": "patients", "Encounter": "encounters", "Condition": "conditions"}
    for rtype, df in frames.items():
        _write(df, out / output_names[rtype], fmt)

    summary = {output_names[rt]: len(frames[rt]) for rt in SUPPORTED_RESOURCE_TYPES}
    summary["bundles_parsed"] = len(bundle_files)
    logger.info("Synthea landing complete: %s", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Land Synthea FHIR Bundles into Bronze.")
    parser.add_argument("--input-dir", required=True, help="Directory containing Synthea *.json bundle files.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    args = parser.parse_args()

    land_synthea(args.input_dir, args.output_dir, args.format)


if __name__ == "__main__":
    sys.exit(main())
