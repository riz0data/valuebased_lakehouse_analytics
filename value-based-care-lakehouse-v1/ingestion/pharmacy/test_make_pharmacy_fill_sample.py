"""
test_make_pharmacy_fill_sample.py

Manual assertion-based tests (pytest not installable in this sandbox).
Run with: python3 test_make_pharmacy_fill_sample.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from make_pharmacy_fill_sample import make_pharmacy_fills, DAYS_SUPPLY_OPTIONS

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

member_bks = ["MBR-001", "MBR-002", "MBR-003"]
drug_bks = ["0069-2587", "0378-3856", "0071-0155"]
pharmacy_bks = ["6789012345"]

fills = make_pharmacy_fills(member_bks, drug_bks, pharmacy_bks)

check("every fill has a member_bk in the input list", all(f["member_bk"] in member_bks for f in fills))
check("every fill has a drug_bk in the input list", all(f["drug_bk"] in drug_bks for f in fills))
check("every fill has a pharmacy_bk in the input list", all(f["pharmacy_bk"] in pharmacy_bks for f in fills))
check("every fill has a valid days_supply", all(f["days_supply"] in DAYS_SUPPLY_OPTIONS for f in fills))
check("every member has at least one fill", {f["member_bk"] for f in fills} == set(member_bks))
check("fill_date values are valid ISO dates", all(len(f["fill_date"]) == 10 and f["fill_date"][4] == "-" for f in fills))

fills_2 = make_pharmacy_fills(member_bks, drug_bks, pharmacy_bks)
check("determinism: same seed produces same output", fills == fills_2)

check("empty member list produces no fills", make_pharmacy_fills([], drug_bks, pharmacy_bks) == [])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
