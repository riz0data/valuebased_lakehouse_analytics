"""
simulate_pipeline_exceptions.py

A runnable, dependency-free demonstration of
pipeline_exception_handler.py's severity tiering across a LOW severity
staging-layer test failure, a MEDIUM severity Vault-layer test failure,
and HIGH severity Vault-load and Gold-layer failures - showing which
ones page a human at the centralized notification address and which
are logged only.

Run it directly: python3 simulate_pipeline_exceptions.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from observability.human_in_the_loop.pipeline_exception_handler import handle_pipeline_exception


def run_simulation():
    print("Simulating four pipeline failures across all severity tiers.\n")

    scenarios = [
        ("dbt_run", "staging.stg_claims", "test_failure",
         "12 rows failed not_null test on claim_id"),
        ("dbt_run", "vault.sat_provider_details", "test_failure",
         "8 rows failed a freshness test on load_date"),
        ("vault_load", "vault.sat_provider_details", "load_error",
         "Satellite load partially failed - 3 of 400 batches errored"),
        ("dbt_run", "gold.fact_claim_payment", "test_failure",
         "relationships test failed - 40 rows reference a missing provider_key"),
    ]

    for pipeline_name, target, failure_type, detail in scenarios:
        exc = handle_pipeline_exception(pipeline_name, target, failure_type, detail)
        notified = "human notified" if exc.human_notified else "logged only, no page"
        print(f"  [{exc.severity.value.upper():<6}] {target} ({failure_type}) -> {notified}\n")


if __name__ == "__main__":
    run_simulation()
