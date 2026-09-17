"""
make_pharmacy_fill_sample.py

Generates SYNTHETIC pharmacy fill transaction fixtures: which member
filled which drug at which pharmacy, and when.

This is the one part of the Pharmacy domain with no real, ingestable
open dataset behind it - the FDA NDC Directory tells us what drugs
exist, and NPPES tells us which NPIs are pharmacies, but neither source
publishes prescription fill events. Real fill data (like real claims
and real member-level HCC scores elsewhere in this repo) is protected
health information that no public dataset exposes at the individual
level. See ingestion/pharmacy/README.md for the full data-honesty note.

Usage:
    python make_pharmacy_fill_sample.py \
        --member-bks MBR-001 MBR-002 \
        --drug-bks 0069-2587 0378-3856 0071-0155 \
        --pharmacy-bks 6789012345 \
        --output-dir ./sample_output
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
from pathlib import Path

DAYS_SUPPLY_OPTIONS = [30, 60, 90]


def make_pharmacy_fills(member_bks: list[str], drug_bks: list[str], pharmacy_bks: list[str],
                          fills_per_member: int = 2, start_date: str = "2024-01-01") -> list[dict]:
    """Generates 1..fills_per_member SYNTHETIC fill events per member,
    each a real-shaped (member, drug, pharmacy, fill_date, days_supply)
    transaction, deterministic under a fixed seed."""
    rng = random.Random(42)
    base_date = dt.date.fromisoformat(start_date)
    rows = []
    for member_bk in member_bks:
        n_fills = rng.randint(1, fills_per_member)
        for i in range(n_fills):
            fill_date = base_date + dt.timedelta(days=rng.randint(0, 300))
            rows.append({
                "member_bk": member_bk,
                "drug_bk": rng.choice(drug_bks),
                "pharmacy_bk": rng.choice(pharmacy_bks),
                "fill_date": fill_date.isoformat(),
                "days_supply": rng.choice(DAYS_SUPPLY_OPTIONS),
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
    parser = argparse.ArgumentParser(description="Generate synthetic pharmacy fill transaction fixtures.")
    parser.add_argument("--member-bks", nargs="+", required=True)
    parser.add_argument("--drug-bks", nargs="+", required=True)
    parser.add_argument("--pharmacy-bks", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    rows = make_pharmacy_fills(args.member_bks, args.drug_bks, args.pharmacy_bks)
    _write_csv(rows, Path(args.output_dir) / "pharmacy_fills.csv")
    print(f"Synthetic pharmacy fill fixtures written to {args.output_dir}")


if __name__ == "__main__":
    main()
