"""
land_ndc.py

Lands the FDA National Drug Code (NDC) Directory into the Bronze layer.

The NDC Directory is a real, public-domain dataset published by the FDA,
distributed as two pipe/tab-delimited text files - product.txt and
package.txt - joined on the PRODUCTID field:
https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
https://www.fda.gov/drugs/drug-approvals-and-databases/ndc-product-file-definitions
https://www.fda.gov/drugs/drug-approvals-and-databases/ndc-package-file-definitions

product.txt: one row per listed drug product (PRODUCTNDC, brand/generic
name, dosage form, labeler, active ingredients, DEA schedule, etc.)
package.txt: one row per package configuration of a product
(NDCPACKAGECODE, package description), linked back via PRODUCTID.

This script reads both files, keeps the real column names (uppercased,
matching the FDA's own field definitions), and writes them to Bronze
largely as-is - unlike Synthea's nested FHIR JSON, these are already flat
tabular files, so there's no flattening step needed, just type/column
hygiene and Bronze metadata columns.

Usage:
    python land_ndc.py --input-dir ./ndc_directory --output-dir ./bronze/ndc
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("land_ndc")

RECORD_SOURCE = "fda_ndc_directory"

# Real FDA NDC Directory field names (product.txt) - see NDC Product File
# Definitions linked above. Kept as-is rather than renamed, to make it
# obvious downstream which fields are FDA's own vs. this repo's naming.
PRODUCT_COLUMNS = [
    "PRODUCTID", "PRODUCTNDC", "PRODUCTTYPENAME", "PROPRIETARYNAME",
    "PROPRIETARYNAMESUFFIX", "NONPROPRIETARYNAME", "DOSAGEFORMNAME",
    "ROUTENAME", "STARTMARKETINGDATE", "ENDMARKETINGDATE",
    "MARKETINGCATEGORYNAME", "APPLICATIONNUMBER", "LABELERNAME",
    "SUBSTANCENAME", "ACTIVE_NUMERATOR_STRENGTH", "ACTIVE_INGRED_UNIT",
    "PHARM_CLASSES", "DEASCHEDULE", "NDC_EXCLUDE_FLAG",
    "LISTING_RECORD_CERTIFIED_THROUGH",
]

# Real FDA NDC Directory field names (package.txt) - see NDC Package File
# Definitions linked above.
PACKAGE_COLUMNS = [
    "PRODUCTID", "PRODUCTNDC", "NDCPACKAGECODE", "PACKAGEDESCRIPTION",
    "STARTMARKETINGDATE", "ENDMARKETINGDATE", "NDC_EXCLUDE_FLAG",
    "SAMPLE_PACKAGE",
]


def _read_ndc_file(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    """FDA ships these tab-delimited despite the .txt extension and the
    documentation's informal references to them as pipe-delimited exports
    in some tooling - the real accessdata.fda.gov ndctext.zip files are
    tab-delimited. Missing/extra columns are tolerated (FDA has added
    columns across years) rather than raising, since the schema evolves."""
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_values=[""])
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        logger.warning("Columns missing from %s (tolerated): %s", path.name, missing)
    return df


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


def land_ndc(input_dir: str, output_dir: str, fmt: str = "parquet") -> dict:
    in_dir = Path(input_dir)
    if not in_dir.exists():
        raise FileNotFoundError(f"NDC input directory not found: {input_dir}")

    product_path = in_dir / "product.txt"
    package_path = in_dir / "package.txt"
    if not product_path.exists() or not package_path.exists():
        raise ValueError(
            f"Expected product.txt and package.txt in {input_dir} "
            "(the real FDA NDC Directory file names)."
        )

    products = _bronze_meta(_read_ndc_file(product_path, PRODUCT_COLUMNS))
    packages = _bronze_meta(_read_ndc_file(package_path, PACKAGE_COLUMNS))

    # Orphan check: every package should reference a real product. Not
    # fatal (FDA data has occasional inconsistencies) but worth logging.
    orphan_packages = packages[~packages["PRODUCTID"].isin(products["PRODUCTID"])]
    if len(orphan_packages) > 0:
        logger.warning("%s package rows reference a PRODUCTID not present in product.txt", len(orphan_packages))

    out = Path(output_dir)
    _write(products, out / "ndc_products", fmt)
    _write(packages, out / "ndc_packages", fmt)

    summary = {
        "ndc_products": len(products),
        "ndc_packages": len(packages),
        "orphan_packages": len(orphan_packages),
    }
    logger.info("NDC landing complete: %s", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Land the FDA NDC Directory into Bronze.")
    parser.add_argument("--input-dir", required=True, help="Directory containing product.txt and package.txt.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--format", dest="fmt", default="parquet", choices=["parquet", "csv"])
    args = parser.parse_args()

    try:
        land_ndc(args.input_dir, args.output_dir, args.fmt)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
