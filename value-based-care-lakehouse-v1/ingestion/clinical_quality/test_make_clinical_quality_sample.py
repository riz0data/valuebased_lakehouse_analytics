"""
test_make_clinical_quality_sample.py

Manual assertion-based tests (pytest is not installable in this sandbox -
see repo-wide environment note). Run with: python3 test_make_clinical_quality_sample.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from make_clinical_quality_sample import (
    make_measures, make_member_measure, make_member_measure_evals, MEASURES, EVAL_RESULTS,
)

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

# 1. Measures: real CMS Star Ratings codes, unique, positive weights
measures = make_measures()
check("measures: unique measure_bk values", len({m["measure_bk"] for m in measures}) == len(measures))
check("measures: all weights positive", all(m["measure_weight"] > 0 for m in measures))
check("measures: contains real CMS codes BCS-E, CBP, COL-E, D09, D10",
      {m["measure_bk"] for m in measures} == {"BCS-E", "CBP", "COL-E", "D09", "D10"})

# 2. Member-measure assignment: every measure_bk assigned is a real declared measure,
#    each member gets 1-3 measures, no duplicate (member, measure) pairs
member_bks = ["MBR-001", "MBR-002", "MBR-003", "MBR-004", "MBR-005"]
member_measure = make_member_measure(member_bks)
measure_bk_set = {bk for bk, _, _ in MEASURES}
check("member_measure: every assigned measure_bk is a real declared measure",
      all(r["measure_bk"] in measure_bk_set for r in member_measure))
pairs = [(r["member_bk"], r["measure_bk"]) for r in member_measure]
check("member_measure: no duplicate (member, measure) pairs", len(pairs) == len(set(pairs)))

from collections import Counter
counts = Counter(r["member_bk"] for r in member_measure)
check("member_measure: each member assigned 1-3 measures", all(1 <= c <= 3 for c in counts.values()))
check("member_measure: every member appears at least once", set(counts.keys()) == set(member_bks))

# 3. Member-measure evals: one eval per pair, results are valid, dates present
evals = make_member_measure_evals(pairs)
check("member_measure_evals: one row per (member, measure) pair", len(evals) == len(pairs))
check("member_measure_evals: all eval_results are valid", all(e["eval_result"] in EVAL_RESULTS for e in evals))
check("member_measure_evals: all rows have an eval_date", all(e["eval_date"] for e in evals))

# 4. Determinism: same seed produces same output across repeated calls
member_measure_2 = make_member_measure(member_bks)
check("determinism: member_measure assignment reproducible with fixed seed",
      member_measure == member_measure_2)
evals_2 = make_member_measure_evals(pairs)
check("determinism: member_measure_evals reproducible with fixed seed", evals == evals_2)

# 5. Empty inputs don't crash
check("empty member list: member_measure returns empty list without crashing", make_member_measure([]) == [])
check("empty pairs list: member_measure_evals returns empty list without crashing",
      make_member_measure_evals([]) == [])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
