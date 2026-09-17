"""
test_land_ndc.py

Manual assertion-based tests (pytest not installable in this sandbox).
Run with: python3 test_land_ndc.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from land_ndc import land_ndc, _read_ndc_file, PRODUCT_COLUMNS, PACKAGE_COLUMNS

passed = 0
failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        print(f"PASS: {name}")
        passed += 1
    else:
        print(f"FAIL: {name}")
        failed += 1

SAMPLE_DIR = Path(__file__).parent / "sample_data"

# 1. Reading product.txt directly
products = _read_ndc_file(SAMPLE_DIR / "product.txt", PRODUCT_COLUMNS)
check("product.txt: all expected FDA columns present", all(c in products.columns for c in PRODUCT_COLUMNS))
check("product.txt: 3 sample products read", len(products) == 3)
check("product.txt: PRODUCTNDC values look like real NDC format", all("-" in v for v in products["PRODUCTNDC"]))

# 2. Reading package.txt directly
packages = _read_ndc_file(SAMPLE_DIR / "package.txt", PACKAGE_COLUMNS)
check("package.txt: all expected FDA columns present", all(c in packages.columns for c in PACKAGE_COLUMNS))
check("package.txt: 4 sample packages read", len(packages) == 4)

# 3. End-to-end landing
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    summary = land_ndc(str(SAMPLE_DIR), tmp, fmt="csv")
    check("land_ndc: summary counts match fixtures", summary == {"ndc_products": 3, "ndc_packages": 4, "orphan_packages": 0})

    out_products = pd.read_csv(Path(tmp) / "ndc_products.csv")
    check("land_ndc: written products file has record_source/load_dts", "record_source" in out_products.columns and "load_dts" in out_products.columns)
    check("land_ndc: record_source is fda_ndc_directory", (out_products["record_source"] == "fda_ndc_directory").all())

    out_packages = pd.read_csv(Path(tmp) / "ndc_packages.csv")
    check("land_ndc: every package PRODUCTID exists in products", set(out_packages["PRODUCTID"]).issubset(set(out_products["PRODUCTID"])))

# 4. Missing directory raises
try:
    land_ndc("/nonexistent/path/xyz", "/tmp/whatever")
    check("land_ndc: raises FileNotFoundError on missing input dir", False)
except FileNotFoundError:
    check("land_ndc: raises FileNotFoundError on missing input dir", True)

# 5. Directory missing product.txt/package.txt raises ValueError
with tempfile.TemporaryDirectory() as tmp:
    empty_dir = Path(tmp) / "empty"
    empty_dir.mkdir()
    try:
        land_ndc(str(empty_dir), str(Path(tmp) / "out"))
        check("land_ndc: raises ValueError when product.txt/package.txt missing", False)
    except ValueError:
        check("land_ndc: raises ValueError when product.txt/package.txt missing", True)

# 6. Orphan package detection (a package referencing a PRODUCTID not in products)
with tempfile.TemporaryDirectory() as tmp:
    bad_dir = Path(tmp) / "bad"
    bad_dir.mkdir()
    (bad_dir / "product.txt").write_text(open(SAMPLE_DIR / "product.txt").read())
    pkg_content = open(SAMPLE_DIR / "package.txt").read()
    pkg_content += "9999-9999_orphan\t9999-9999\t9999-9999-01\t1 BOTTLE\t20200101\t\tN\tN\n"
    (bad_dir / "package.txt").write_text(pkg_content)
    summary = land_ndc(str(bad_dir), str(Path(tmp) / "out"), fmt="csv")
    check("land_ndc: detects 1 orphan package row", summary["orphan_packages"] == 1)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
