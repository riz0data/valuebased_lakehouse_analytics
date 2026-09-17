"""
make_payment_integrity_sample.py

Generates small SYNTHETIC fixture files for the Payment Integrity entities
that have no real open-data source: VBC Contracts, Prior Authorizations,
Appeals, and claim-level Payment / Adjustment / COB Recovery transactions.

Unlike NPPES, DE-SynPUF, and Synthea, there is no public open dataset for
managed-care contract terms, prior-auth workflows, or payment/adjustment
transaction detail - these are proprietary payer operational data in the
real world. This generator fabricates a small, clearly-synthetic dataset
in a realistic shape so the Payment Integrity Vault models have something
real to build and test against, and are runnable end-to-end.

This is explicitly flagged in ingestion/payment_integrity/README.md -
these files are NOT derived from CMS, Synthea, or NPPES; they are
fabricated for demonstration purposes only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
from pathlib import Path

random.seed(42)  # deterministic output for reproducible tests

CONTRACT_MODELS = ["MSSP", "capitated", "shared_savings"]
AUTH_STATUSES = ["approved", "denied", "pending"]
APPEAL_STATUSES = ["upheld", "overturned", "pending"]
APPEAL_REASONS = ["medical_necessity", "coding_error", "timely_filing", "coverage_determination"]
ADJUSTMENT_REASON_CODES = ["CO-45", "CO-97", "PR-1", "OA-23"]


def make_contracts(n: int) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "contract_bk": f"CONTRACT-{i:04d}",
            "contract_model": random.choice(CONTRACT_MODELS),
            "effective_date": (dt.date(2023, 1, 1) + dt.timedelta(days=random.randint(0, 700))).isoformat(),
        })
    return rows


def make_provider_contracts(provider_bks: list[str], contract_bks: list[str]) -> list[dict]:
    """Each provider is attached to 1-2 contracts."""
    rows = []
    for p in provider_bks:
        for c in random.sample(contract_bks, k=random.randint(1, min(2, len(contract_bks)))):
            rows.append({"provider_bk": p, "contract_bk": c})
    return rows


def make_authorizations(claim_bks: list[str], n: int) -> list[dict]:
    rows = []
    sampled_claims = random.sample(claim_bks, k=min(n, len(claim_bks)))
    for i, claim_bk in enumerate(sampled_claims, start=1):
        rows.append({
            "authorization_bk": f"AUTH-{i:04d}",
            "claim_line_bk": claim_bk,
            "auth_status": random.choice(AUTH_STATUSES),
            "requested_date": (dt.date(2024, 1, 1) + dt.timedelta(days=random.randint(0, 300))).isoformat(),
        })
    return rows


def make_appeals(claim_bks: list[str], n: int) -> list[dict]:
    rows = []
    sampled_claims = random.sample(claim_bks, k=min(n, len(claim_bks)))
    for i, claim_bk in enumerate(sampled_claims, start=1):
        rows.append({
            "appeal_bk": f"APPEAL-{i:04d}",
            "claim_line_bk": claim_bk,
            "appeal_status": random.choice(APPEAL_STATUSES),
            "appeal_reason": random.choice(APPEAL_REASONS),
        })
    return rows


def make_payment_txns(claim_bks: list[str]) -> list[dict]:
    rows = []
    for i, claim_bk in enumerate(claim_bks, start=1):
        billed = round(random.uniform(2000, 50000), 2)
        allowed = round(billed * random.uniform(0.6, 0.95), 2)
        paid = round(allowed * random.uniform(0.85, 1.0), 2)
        rows.append({
            "txn_bk": f"PAYTXN-{i:04d}",
            "claim_line_bk": claim_bk,
            "billed_amount": billed,
            "allowed_amount": allowed,
            "paid_amount": paid,
            "payment_date": (dt.date(2024, 2, 1) + dt.timedelta(days=random.randint(0, 300))).isoformat(),
        })
    return rows


def make_adjustment_txns(claim_bks: list[str], n: int) -> list[dict]:
    rows = []
    sampled_claims = random.sample(claim_bks, k=min(n, len(claim_bks)))
    for i, claim_bk in enumerate(sampled_claims, start=1):
        rows.append({
            "txn_bk": f"ADJTXN-{i:04d}",
            "claim_line_bk": claim_bk,
            "adjustment_amount": round(random.uniform(-500, 500), 2),
            "adjustment_reason_code": random.choice(ADJUSTMENT_REASON_CODES),
            "adjustment_date": (dt.date(2024, 3, 1) + dt.timedelta(days=random.randint(0, 200))).isoformat(),
        })
    return rows


def make_cob_recovery_txns(claim_bks: list[str], n: int) -> list[dict]:
    rows = []
    sampled_claims = random.sample(claim_bks, k=min(n, len(claim_bks)))
    for i, claim_bk in enumerate(sampled_claims, start=1):
        rows.append({
            "txn_bk": f"COBTXN-{i:04d}",
            "claim_line_bk": claim_bk,
            "recovery_amount": round(random.uniform(100, 5000), 2),
            "recovery_date": (dt.date(2024, 4, 1) + dt.timedelta(days=random.randint(0, 200))).isoformat(),
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
    parser = argparse.ArgumentParser(description="Generate synthetic Payment Integrity fixtures.")
    parser.add_argument("--claim-bks", nargs="+", required=True, help="Existing claim_line_bk values to attach transactions to.")
    parser.add_argument("--provider-bks", nargs="+", required=True, help="Existing provider_bk values to attach contracts to.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)

    contracts = make_contracts(n=3)
    contract_bks = [c["contract_bk"] for c in contracts]
    _write_csv(contracts, out / "contracts.csv")
    _write_csv(make_provider_contracts(args.provider_bks, contract_bks), out / "provider_contracts.csv")
    _write_csv(make_authorizations(args.claim_bks, n=max(1, len(args.claim_bks) // 2)), out / "authorizations.csv")
    _write_csv(make_appeals(args.claim_bks, n=max(1, len(args.claim_bks) // 3)), out / "appeals.csv")
    _write_csv(make_payment_txns(args.claim_bks), out / "payment_transactions.csv")
    _write_csv(make_adjustment_txns(args.claim_bks, n=max(1, len(args.claim_bks) // 2)), out / "adjustment_transactions.csv")
    _write_csv(make_cob_recovery_txns(args.claim_bks, n=max(1, len(args.claim_bks) // 4)), out / "cob_recovery_transactions.csv")

    print(f"Synthetic Payment Integrity fixtures written to {out}")


if __name__ == "__main__":
    main()
