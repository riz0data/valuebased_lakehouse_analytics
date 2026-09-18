"""
model_gateway.py

Reference implementation of an AI gateway: a single choke point that
every outbound call to a language model passes through, distinct from
and complementary to the MCP layer (.mcp/mcp.json.example), which
governs the agent-to-tool leg of traffic, not the agent-to-model leg.

Where AI gateways manage the conversation between agent and model,
MCP gateways manage the conversation between agent and tools (see
docs/decisions/ADRs.md ADR-015 for sources). This module is concerned
only with the model leg: which provider a request goes to, whether it
is within budget, and whether its content clears a basic policy check
before it is sent and after a response comes back. It does not touch
tool execution, row filters, or semantic-layer access - those remain
governed by ADR-006, ADR-007, and the MCP config exactly as before.

This is a reference implementation with a single mocked provider
(no real network calls, no API keys required), sized to demonstrate
the pattern: control plane (policy/budget/routing decisions) separated
from data plane (the actual request/response handling), matching the
split-plane architecture real AI gateways use.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Control plane: policy, budget, and routing rules. In a real deployment
# this configuration would live outside the application and be updated
# without redeploying agent code - kept as plain data here for clarity.
# ---------------------------------------------------------------------------

PROVIDER_RATES_PER_1K_TOKENS = {
    # illustrative rates, not live pricing - mirrors the pattern already
    # used in observability/finops/agent_cost_tracker.py
    "provider-a-large": 0.015,
    "provider-a-small": 0.002,
    "provider-b-large": 0.012,
}

DAILY_BUDGET_USD_BY_FEATURE = {
    "semantic-layer-qa": 5.00,
    "metric-lookup": 2.00,
}

DENIED_CONTENT_MARKERS = (
    "ssn", "social security number", "patient full name and dob",
)


class BudgetExceededError(Exception):
    """Raised when a request would push a feature's daily spend over its
    configured budget. The gateway refuses to place the call - the same
    enforce-outside-the-model principle used by approval_gate.py and
    sub_agent_delegation.py."""
    pass


class ContentPolicyError(Exception):
    """Raised when a request or response trips a basic content policy
    check. This is a deliberately simple placeholder - a real deployment
    would use a proper PII/content-safety classifier, not substring
    matching."""
    pass


@dataclass
class GatewayRequest:
    request_id: str
    feature: str
    provider: str
    prompt_tokens: int
    max_completion_tokens: int
    content_preview: str


@dataclass
class GatewayResponse:
    request_id: str
    provider: str
    completion_tokens: int
    cost_usd: float
    timestamp_utc: str


# In-memory spend ledger, same pattern as agent_cost_tracker.py's
# per-feature rollup - a real deployment would back this with the same
# Delta table already used for audit and cost events.
_SPEND_LEDGER: dict[str, float] = {}
_REQUEST_LOG: list[GatewayResponse] = []


def _check_content_policy(text: str) -> None:
    lowered = text.lower()
    for marker in DENIED_CONTENT_MARKERS:
        if marker in lowered:
            raise ContentPolicyError(
                f"Request blocked by gateway content policy: contains disallowed pattern '{marker}'."
            )


def _check_budget(feature: str, projected_cost: float) -> None:
    spent_today = _SPEND_LEDGER.get(feature, 0.0)
    budget = DAILY_BUDGET_USD_BY_FEATURE.get(feature)
    if budget is not None and spent_today + projected_cost > budget:
        raise BudgetExceededError(
            f"Request refused: feature '{feature}' has spent "
            f"{spent_today:.4f} of its {budget:.2f} daily budget; "
            f"this call would add {projected_cost:.4f} and exceed it."
        )


def route_request(feature: str, content: str, prompt_tokens: int,
                   max_completion_tokens: int,
                   preferred_provider: str = "provider-a-large") -> GatewayRequest:
    """
    The single entry point an agent calls instead of reaching a model
    provider directly. Applies content policy and budget checks before
    a call is allowed to proceed, then returns a GatewayRequest record
    representing the (mocked) outbound call.
    """
    _check_content_policy(content)

    rate = PROVIDER_RATES_PER_1K_TOKENS.get(preferred_provider)
    if rate is None:
        raise ValueError(f"Unknown provider '{preferred_provider}'.")

    projected_tokens = prompt_tokens + max_completion_tokens
    projected_cost = (projected_tokens / 1000) * rate
    _check_budget(feature, projected_cost)

    return GatewayRequest(
        request_id=str(uuid.uuid4()),
        feature=feature,
        provider=preferred_provider,
        prompt_tokens=prompt_tokens,
        max_completion_tokens=max_completion_tokens,
        content_preview=content[:80],
    )


def record_response(request: GatewayRequest, actual_completion_tokens: int,
                     response_text: str) -> GatewayResponse:
    """
    Called after the (mocked) model call returns. Runs the content
    policy check again on the response side - a gateway inspects both
    legs of the conversation, not just the outbound prompt - and books
    the actual cost against the feature's daily spend ledger.
    """
    _check_content_policy(response_text)

    rate = PROVIDER_RATES_PER_1K_TOKENS[request.provider]
    actual_tokens = request.prompt_tokens + actual_completion_tokens
    actual_cost = (actual_tokens / 1000) * rate

    _SPEND_LEDGER[request.feature] = _SPEND_LEDGER.get(request.feature, 0.0) + actual_cost

    response = GatewayResponse(
        request_id=request.request_id,
        provider=request.provider,
        completion_tokens=actual_completion_tokens,
        cost_usd=actual_cost,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    _REQUEST_LOG.append(response)
    return response


def daily_spend_by_feature() -> dict:
    """Rollup of spend booked so far, mirroring
    agent_cost_tracker.py's daily_cost_by_feature()."""
    return dict(_SPEND_LEDGER)


if __name__ == "__main__":
    print(
        "This module defines a reference AI gateway: a single choke "
        "point for model-leg traffic covering routing, budget "
        "enforcement, and basic content policy, separate from the "
        "MCP layer which governs agent-to-tool traffic. Run "
        "simulate_gateway.py for a runnable demonstration."
    )
