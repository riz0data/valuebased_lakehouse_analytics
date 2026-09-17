"""
make_risk_adjustment_sample.py

Generates small SYNTHETIC fixture files for the Risk Adjustment entities
that have no ingestable open-data source in this repo: the
Diagnosis-to-HCC crosswalk, Member-HCC assignment (now with coding-gap
lifecycle fields), and Member Risk Score (RAF) transactions.

Real, public facts used as the basis for these fixtures (not fabricated):
- CMS-HCC model versions V24 and V28 are real, CMS-published risk
  adjustment model versions - V28 is the current model as of 2024,
  replacing V24. (Source: CMS 2024 Rate Announcement / OIG reporting.)
- The HCC category numbers used below (e.g. HCC 18/19/37/38 for
  diabetes-related categories) are real CMS-HCC V28 category numbers,
  not invented ones.

What IS fabricated: which specific members are assigned which HCCs, the
RAF score values themselves, and the coding-gap lifecycle dates below -
CMS does not publish member-level risk scores (that's the entire point
of them being computed, per-beneficiary, private data), so any
member-level RAF value or coding-gap event in this repo is for
demonstration purposes only and carries no real predictive meaning.

See ingestion/risk_adjustment/README.md for the full data-honesty note.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
from pathlib import Path

# Real CMS-HCC V28 category numbers and descriptions (a representative subset,
# not the full 115-category list) - see
# https://www.cms.gov/files/document/2024-midyear-final-call-letter.pdf and
# related CMS V28 model documentation for the authoritative full list.
HCC_CATEGORIES = [
    ("HCC8",  "Metastatic Cancer and Acute Leukemia"),
    ("HCC18", "Diabetes with Chronic Complications"),
    ("HCC38", "Rheumatoid Arthritis and Inflammatory Connective Tissue Disease"),
    ("HCC85", "Congestive Heart Failure"),
    ("HCC111", "Chronic Obstructive Pulmonary Disease"),
    ("HCC138", "Chronic Kidney Disease, Stage 5"),
]

RISK_MODELS = [
    ("CMS-HCC-V24", "CMS-HCC V24"),
    ("CMS-HCC-V28", "CMS-HCC V28"),
]

# ICD-10-CM codes plausible for each HCC category, used to build a
# demonstration diagnosis-to-HCC crosswalk. These are real, valid
# ICD-10-CM code formats/prefixes for the associated conditions, but the
# crosswall to HCC below is illustrative, not the authoritative CMS
# mapping file (which is a large published lookup table).
DIAGNOSIS_TO_HCC_SAMPLE = {
    "C7800": "HCC8",
    "E1122": "HCC18",
    "M0600": "HCC38",
    "I5023": "HCC85",
    "J449":  "HCC111",
    "N185":  "HCC138",
}


def make_risk_models() -> list[dict]:
    return [{"risk_model_bk": bk, "model_name": name} for bk, name in RISK_MODELS]


def make_hcc_categories() -> list[dict]:
    rng = random.Random(42)
    return [{"hcc_bk": bk, "hcc_description": desc, "hcc_weight": round(rng.uniform(0.15, 1.2), 3)}
            for bk, desc in HCC_CATEGORIES]


def make_diagnosis_hcc_crosswalk(diagnosis_bks: list[str]) -> list[dict]:
    """Maps each given diagnosis code to an HCC if we have a sample mapping for it."""
    rows = []
    for dbk in diagnosis_bks:
        hcc_bk = DIAGNOSIS_TO_HCC_SAMPLE.get(dbk)
        if hcc_bk:
            for risk_model_bk, _ in RISK_MODELS:
                rows.append({"diagnosis_bk": dbk, "hcc_bk": hcc_bk, "risk_model_bk": risk_model_bk})
    return rows


def make_member_hcc(member_bks: list[str], base_date: str = "2024-01-01") -> list[dict]:
    """Randomly assigns 0-2 HCCs to each member (SYNTHETIC assignment),
    now also emitting a coding-gap lifecycle per assignment:
    - active_flag: whether the HCC is still considered active/coded
    - coding_gap_identified_date: when a suspected-but-uncoded gap was
      identified for this member-HCC pair (always populated here, so
      Coding Gap Closure Rate has a real denominator)
    - coding_gap_closed_date: when/if that gap was subsequently closed
      by confirming the code (populated for ~60% of gaps, else blank -
      an open gap), which is what drives Coding Gap Closure Rate's
      numerator.
    """
    rng = random.Random(42)
    rows = []
    hcc_bks = [bk for bk, _ in HCC_CATEGORIES]
    start = dt.date.fromisoformat(base_date)
    for m in member_bks:
        for hcc_bk in rng.sample(hcc_bks, k=rng.randint(0, 2)):
            identified = start + dt.timedelta(days=rng.randint(0, 120))
            closed = None
            if rng.random() < 0.6:
                closed = identified + dt.timedelta(days=rng.randint(5, 90))
            rows.append({
                "member_bk": m,
                "hcc_bk": hcc_bk,
                "active_flag": "Y" if closed is not None else "N",
                "coding_gap_identified_date": identified.isoformat(),
                "coding_gap_closed_date": closed.isoformat() if closed else "",
            })
    return rows


def make_suspected_hcc(member_bks: list[str]) -> list[dict]:
    """SYNTHETIC 'suspected' HCCs per member - representing what a
    clinical-evidence suspecting engine (e.g. claims/labs/notes analysis)
    would flag as a plausible-but-not-yet-coded HCC for a member. This is
    a separate, deliberately fabricated fixture from make_member_hcc's
    'captured/coded' HCCs, because the two need to differ for HCC Capture
    Rate and Suspecting Yield Rate to mean anything - if they were
    computed from the exact same source rows, capture rate would
    trivially always be 100%.

    Note on why this can't be derived from real diagnosis data in this
    repo: the CMS-HCC diagnosis-to-HCC crosswalk is ICD-10-CM only (HCC
    risk adjustment has used ICD-10-CM exclusively since the 2015 ICD-9
    to ICD-10 transition), but this repo's real diagnosis data is
    ICD-9-CM (DE-SynPUF) or SNOMED CT (Synthea) - see ADR-004 in
    docs/decisions/ADRs.md. Cross-walking either to ICD-10-CM is out of
    scope for a portfolio project (the same reasoning ADR-004 already
    applies to not cross-walking SNOMED to ICD), so "suspected HCC" here
    is a labeled synthetic fixture rather than a suspecting-engine result
    derived from this repo's own diagnosis data.
    """
    rng = random.Random(43)
    rows = []
    hcc_bks = [bk for bk, _ in HCC_CATEGORIES]
    for m in member_bks:
        for hcc_bk in rng.sample(hcc_bks, k=rng.randint(1, 3)):
            rows.append({"member_bk": m, "hcc_bk": hcc_bk})
    return rows


def make_member_risk_scores(member_bks: list[str]) -> list[dict]:
    """One RAF score per member per model year - SYNTHETIC values."""
    rng = random.Random(42)
    rows = []
    for m in member_bks:
        for model_year in (2023, 2024):
            risk_model_bk = "CMS-HCC-V24" if model_year == 2023 else "CMS-HCC-V28"
            rows.append({
                "member_bk": m,
                "risk_model_bk": risk_model_bk,
                "raf_score": round(rng.uniform(0.6, 2.8), 3),
                "model_year": model_year,
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
    parser = argparse.ArgumentParser(description="Generate synthetic Risk Adjustment fixtures.")
    parser.add_argument("--member-bks", nargs="+", required=True)
    parser.add_argument("--diagnosis-bks", nargs="+", default=list(DIAGNOSIS_TO_HCC_SAMPLE.keys()))
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    _write_csv(make_risk_models(), out / "risk_models.csv")
    _write_csv(make_hcc_categories(), out / "hcc_categories.csv")
    _write_csv(make_diagnosis_hcc_crosswalk(args.diagnosis_bks), out / "diagnosis_hcc_crosswalk.csv")
    _write_csv(make_member_hcc(args.member_bks), out / "member_hcc.csv")
    _write_csv(make_suspected_hcc(args.member_bks), out / "suspected_hcc.csv")
    _write_csv(make_member_risk_scores(args.member_bks), out / "member_risk_scores.csv")

    print(f"Synthetic Risk Adjustment fixtures written to {out}")


if __name__ == "__main__":
    main()
