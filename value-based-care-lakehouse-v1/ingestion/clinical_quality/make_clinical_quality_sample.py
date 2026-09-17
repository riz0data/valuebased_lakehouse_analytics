"""
make_clinical_quality_sample.py

Generates small SYNTHETIC fixture files for the Clinical Quality entities
with no ingestable open-data source in this repo: the Measure dimension
(seeded with real CMS Star Ratings measure codes) and the
Member-Measure / Member-Measure-Eval facts.

Real, public facts used as the basis for these fixtures (not fabricated):
- The measure codes and names below (BCS-E, CBP, COL-E, D09, D10) are
  real CMS Star Ratings measure codes/names, published annually in the
  CMS Part C & D Star Ratings Technical Notes (cms.gov). The measure
  weights are illustrative of the real Star Ratings weighting concept
  (CMS does weight some measures like Controlling Blood Pressure more
  heavily than others) but are NOT copied verbatim from a specific
  year's technical notes - see README for the caveat.

What IS fabricated: which specific members are evaluated against which
measures, and every member-level evaluation result (met/not met). CMS
Star Ratings are published at the CONTRACT (health plan) level, not the
member level - a member-level "did this person get their breast cancer
screening" evaluation is exactly the kind of record real payers hold
privately and CMS never publishes, so there is no real data to
substitute here.

See ingestion/clinical_quality/README.md for the full data-honesty note.
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

# Real CMS Star Ratings measure codes and names (a representative subset,
# not the full measure set for a given year - see
# https://www.cms.gov/files/document/2024-star-ratings-technical-notes.pdf
# and successor-year technical notes for the authoritative full list).
MEASURES = [
    ("BCS-E", "Breast Cancer Screening", 1.0),
    ("CBP",   "Controlling High Blood Pressure", 3.0),
    ("COL-E", "Colorectal Cancer Screening", 1.0),
    ("D09",   "Medication Adherence for Hypertension (RAS antagonists)", 3.0),
    ("D10",   "Medication Adherence for Cholesterol (Statins)", 3.0),
]

EVAL_RESULTS = ["met", "not_met"]


def make_measures() -> list[dict]:
    return [{"measure_bk": bk, "measure_name": name, "measure_weight": weight}
            for bk, name, weight in MEASURES]


def make_member_measure(member_bks: list[str]) -> list[dict]:
    """Assigns each member to 1-3 measures they're eligible for - SYNTHETIC assignment."""
    rng = random.Random(42)
    measure_bks = [bk for bk, _, _ in MEASURES]
    rows = []
    for m in member_bks:
        for measure_bk in rng.sample(measure_bks, k=rng.randint(1, 3)):
            rows.append({"member_bk": m, "measure_bk": measure_bk})
    return rows


def make_member_measure_evals(member_measure_pairs: list[tuple[str, str]],
                               eval_date: str = "2024-12-31") -> list[dict]:
    """One evaluation result per (member, measure) pair - SYNTHETIC results."""
    rng = random.Random(42)
    rows = []
    for member_bk, measure_bk in member_measure_pairs:
        rows.append({
            "member_bk": member_bk,
            "measure_bk": measure_bk,
            "eval_result": rng.choice(EVAL_RESULTS),
            "eval_date": eval_date,
        })
    return rows


def _write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Clinical Quality fixtures.")
    parser.add_argument("--member-bks", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    _write_csv(make_measures(), out / "measures.csv")

    member_measure = make_member_measure(args.member_bks)
    _write_csv(member_measure, out / "member_measure.csv")

    pairs = [(r["member_bk"], r["measure_bk"]) for r in member_measure]
    evals = make_member_measure_evals(pairs)
    _write_csv(evals, out / "member_measure_evals.csv")

    print(f"Synthetic Clinical Quality fixtures written to {out}")


if __name__ == "__main__":
    main()
