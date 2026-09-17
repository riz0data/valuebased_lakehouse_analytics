"""
test_make_risk_adjustment_sample.py

Manual assertion-based tests (pytest is not installable in this sandbox -
see repo-wide environment note). Run with: python3 test_make_risk_adjustment_sample.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from make_risk_adjustment_sample import (
    make_risk_models, make_hcc_categories, make_diagnosis_hcc_crosswalk,
    make_member_hcc, make_member_risk_scores, make_suspected_hcc,
    DIAGNOSIS_TO_HCC_SAMPLE, HCC_CATEGORIES,
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

models = make_risk_models()
check("risk_models: exactly 2 rows", len(models) == 2)
check("risk_models: contains CMS-HCC V24 and V28",
      {m["model_name"] for m in models} == {"CMS-HCC V24", "CMS-HCC V28"})

hccs = make_hcc_categories()
check("hcc_categories: unique hcc_bk values", len({h["hcc_bk"] for h in hccs}) == len(hccs))
check("hcc_categories: all weights positive", all(h["hcc_weight"] > 0 for h in hccs))
check("hcc_categories: matches real CMS HCC count", len(hccs) == len(HCC_CATEGORIES))

diag_bks = list(DIAGNOSIS_TO_HCC_SAMPLE.keys())
crosswalk = make_diagnosis_hcc_crosswalk(diag_bks)
hcc_bk_set = {bk for bk, _ in HCC_CATEGORIES}
model_bk_set = {"CMS-HCC-V24", "CMS-HCC-V28"}
check("crosswalk: every hcc_bk is a real declared HCC", all(r["hcc_bk"] in hcc_bk_set for r in crosswalk))
check("crosswalk: every risk_model_bk is a declared model", all(r["risk_model_bk"] in model_bk_set for r in crosswalk))
check("crosswalk: each mapped diagnosis appears once per model (2 rows each)",
      len(crosswalk) == len(diag_bks) * 2)

crosswalk_unmapped = make_diagnosis_hcc_crosswalk(["Z9999", "UNKNOWNCODE"])
check("crosswalk: unmapped diagnosis codes produce zero rows (no fabricated mappings)",
      len(crosswalk_unmapped) == 0)

member_bks = ["MBR-001", "MBR-002", "MBR-003", "MBR-004", "MBR-005"]
member_hcc = make_member_hcc(member_bks)
check("member_hcc: every assigned hcc_bk is a real declared HCC", all(r["hcc_bk"] in hcc_bk_set for r in member_hcc))
member_hcc_pairs = [(r["member_bk"], r["hcc_bk"]) for r in member_hcc]
check("member_hcc: no duplicate (member, hcc) pairs", len(member_hcc_pairs) == len(set(member_hcc_pairs)))

scores = make_member_risk_scores(member_bks)
check("member_risk_scores: 2 rows per member (one per model year)", len(scores) == len(member_bks) * 2)
check("member_risk_scores: all RAF scores positive", all(s["raf_score"] > 0 for s in scores))
check("member_risk_scores: model_year in (2023, 2024)", all(s["model_year"] in (2023, 2024) for s in scores))
check("member_risk_scores: risk_model_bk correctly tied to model_year",
      all((s["model_year"] == 2023 and s["risk_model_bk"] == "CMS-HCC-V24") or
          (s["model_year"] == 2024 and s["risk_model_bk"] == "CMS-HCC-V28") for s in scores))

hccs2 = make_hcc_categories()
check("determinism: hcc_weight values are reproducible with fixed seed",
      [h["hcc_weight"] for h in hccs] == [h["hcc_weight"] for h in hccs2])

check("empty member list: member_hcc returns empty list without crashing", make_member_hcc([]) == [])
check("empty member list: member_risk_scores returns empty list without crashing", make_member_risk_scores([]) == [])


# --- coding-gap lifecycle fields (added for Coding Gap Closure Rate) ---
check("member_hcc: every row has active_flag Y or N", all(r["active_flag"] in ("Y", "N") for r in member_hcc))
check("member_hcc: every row has a coding_gap_identified_date", all(r["coding_gap_identified_date"] for r in member_hcc))
check("member_hcc: active_flag Y implies a non-empty coding_gap_closed_date",
      all((r["active_flag"] == "N") or (r["active_flag"] == "Y" and r["coding_gap_closed_date"]) for r in member_hcc))
check("member_hcc: active_flag N implies an empty coding_gap_closed_date",
      all(r["coding_gap_closed_date"] == "" for r in member_hcc if r["active_flag"] == "N"))
member_hcc_2 = make_member_hcc(member_bks)
check("member_hcc: determinism - same seed produces same coding-gap dates", member_hcc == member_hcc_2)


# --- suspected HCC fixture (added for HCC Capture Rate / Suspecting Yield Rate) ---
suspected = make_suspected_hcc(member_bks)
check("suspected_hcc: every assigned hcc_bk is a real declared HCC", all(r["hcc_bk"] in hcc_bk_set for r in suspected))
suspected_pairs = [(r["member_bk"], r["hcc_bk"]) for r in suspected]
check("suspected_hcc: no duplicate (member, hcc) pairs", len(suspected_pairs) == len(set(suspected_pairs)))
check("suspected_hcc: every member has at least one suspected HCC", {r["member_bk"] for r in suspected} == set(member_bks))
suspected_2 = make_suspected_hcc(member_bks)
check("suspected_hcc: determinism - same seed produces same output", suspected == suspected_2)
check("suspected_hcc: empty member list returns empty list without crashing", make_suspected_hcc([]) == [])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
