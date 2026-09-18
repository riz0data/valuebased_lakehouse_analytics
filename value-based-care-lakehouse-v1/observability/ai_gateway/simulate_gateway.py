"""
simulate_gateway.py

Runnable, dependency-free demonstration of model_gateway.py: a normal
allowed call, a call refused for tripping the content policy, and a
call refused for exceeding its feature's daily budget.

Run it directly: python3 simulate_gateway.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from observability.ai_gateway.model_gateway import (
    route_request, record_response, daily_spend_by_feature,
    BudgetExceededError, ContentPolicyError,
)


def run_simulation():
    print("Scenario 1: a normal, allowed request through the gateway.")
    req = route_request(
        feature="metric-lookup",
        content="What was the Medical Loss Ratio for Q2?",
        prompt_tokens=120,
        max_completion_tokens=200,
        preferred_provider="provider-a-small",
    )
    resp = record_response(req, actual_completion_tokens=150,
                            response_text="The Medical Loss Ratio for Q2 was 84.3 percent.")
    print(f"  Allowed. provider={resp.provider} cost_usd={resp.cost_usd:.5f}\n")

    print("Scenario 2: a request that trips the content policy and is refused.")
    try:
        route_request(
            feature="metric-lookup",
            content="Look up the patient full name and DOB for member 12345.",
            prompt_tokens=100,
            max_completion_tokens=100,
        )
        print("  ERROR: this should have been refused and was not.")
    except ContentPolicyError as e:
        print(f"  Refused, as required: {e}\n")

    print("Scenario 3: repeated calls that exceed the feature's daily budget "
          "(metric-lookup is capped at 2.00 dollars per day).")
    try:
        for i in range(200):
            req = route_request(
                feature="metric-lookup",
                content=f"Metric lookup number {i}",
                prompt_tokens=500,
                max_completion_tokens=500,
                preferred_provider="provider-a-large",
            )
            record_response(req, actual_completion_tokens=500,
                             response_text=f"Result for lookup {i}")
        print("  ERROR: budget should have been exceeded before 200 calls completed.")
    except BudgetExceededError as e:
        print(f"  Refused after {len(daily_spend_by_feature())} feature(s) tracked, as required: {e}\n")

    print("Spend booked so far, by feature:")
    for feature, spent in daily_spend_by_feature().items():
        print(f"  {feature}: {spent:.4f} dollars")


if __name__ == "__main__":
    run_simulation()
