"""
Unit tests for make_payment_integrity_sample.py - the synthetic fixture
generator for Payment Integrity entities with no open-data source
(VBC contracts, prior authorizations, appeals, payment/adjustment/COB
recovery transactions).
"""
from make_payment_integrity_sample import (
    make_contracts, make_provider_contracts, make_authorizations,
    make_appeals, make_payment_txns, make_adjustment_txns, make_cob_recovery_txns,
)

CLAIMS = ["CLM-001", "CLM-002", "CLM-003", "CLM-004"]
PROVIDERS = ["NPI-1111111111", "NPI-2222222222"]


def test_make_contracts_count_and_shape():
    contracts = make_contracts(3)
    assert len(contracts) == 3
    assert all(set(c.keys()) == {"contract_bk", "contract_model", "effective_date"} for c in contracts)
    assert len({c["contract_bk"] for c in contracts}) == 3


def test_make_provider_contracts_covers_every_provider():
    contracts = make_contracts(3)
    contract_bks = [c["contract_bk"] for c in contracts]
    pc = make_provider_contracts(PROVIDERS, contract_bks)
    covered_providers = {row["provider_bk"] for row in pc}
    assert covered_providers == set(PROVIDERS)
    assert all(row["contract_bk"] in contract_bks for row in pc)


def test_make_authorizations_references_real_claims():
    auths = make_authorizations(CLAIMS, n=2)
    assert len(auths) == 2
    assert all(row["claim_line_bk"] in CLAIMS for row in auths)
    assert all(row["auth_status"] in {"approved", "denied", "pending"} for row in auths)


def test_make_appeals_references_real_claims():
    appeals = make_appeals(CLAIMS, n=1)
    assert len(appeals) == 1
    assert appeals[0]["claim_line_bk"] in CLAIMS


def test_make_payment_txns_one_per_claim_and_amounts_ordered():
    txns = make_payment_txns(CLAIMS)
    assert len(txns) == len(CLAIMS)
    for t in txns:
        assert t["billed_amount"] >= t["allowed_amount"] >= t["paid_amount"] > 0


def test_make_adjustment_txns_reference_real_claims():
    adj = make_adjustment_txns(CLAIMS, n=2)
    assert len(adj) == 2
    assert all(row["claim_line_bk"] in CLAIMS for row in adj)


def test_make_cob_recovery_txns_reference_real_claims_and_positive_amounts():
    cob = make_cob_recovery_txns(CLAIMS, n=1)
    assert len(cob) == 1
    assert cob[0]["claim_line_bk"] in CLAIMS
    assert cob[0]["recovery_amount"] > 0


def test_sampling_never_exceeds_available_claims():
    auths = make_authorizations(CLAIMS, n=999)
    assert len(auths) == len(CLAIMS)
