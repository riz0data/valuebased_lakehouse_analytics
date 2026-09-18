"""
end_to_end_orchestrator.py

The single script that answers the question every other module in
observability/ was built to support: what actually happens, step by
step, when a person asks this system a plain-language question.

This chains together every layer built across this project's agentic
AI architecture, in the order they would actually fire on a real
request:

  1. Identity        - the request is tagged with the agent's own
                        service-principal identity (identity/), never
                        a human credential, before anything else happens.
  2. Guardrails       - pre-call input screening (guardrails.py):
                        blocks prompt injection, redacts sensitive data
                        typed into the question itself.
  3. AI Gateway       - the model-leg call (ai_gateway/model_gateway.py):
                        budget check and content policy on the call to
                        the language model, separate from tool access.
  4. Orchestration    - if the task is split into sub-steps, constrained
                        delegation (orchestration/sub_agent_delegation.py)
                        ensures any sub-agent gets no more access than
                        the parent held.
  5. MCP / Semantic layer access - the tool-call leg: the agent may only
                        reach gold.semantic (ADR-006), never raw tables.
  6. Human-in-the-loop - the approval gate (approval_gate.py) sits in
                        front of the actual query execution; Tier 1
                        read-only lookups auto-approve, anything riskier
                        would halt here pending a human.
  7. Governed query execution - the semantic layer sits on top of Unity
                        Catalog row filters/column masks (ADR-007) -
                        represented here rather than actually executed,
                        since this is a portfolio project with no live
                        warehouse connection.
  8. Guardrails (post-call) - validates the resolved metric is real
                        before it's allowed to reach the user.
  9. Audit + cost logging - every hop is logged (mirroring
                        mcp_audit_logger.py's ToolCallEvent) and cost is
                        booked against both the AI gateway's ledger and
                        the FinOps agent cost tracker's pattern.
  10. Summary          - a plain-language answer is returned to the user.

This is a reference orchestration, not a live agent loop: there is no
real language model call and no live warehouse connection. Steps that
would call an LLM or run a SQL query are represented by realistic
mocked results, so the full control flow - especially every enforcement
point - is genuine, runnable, and inspectable end to end, exactly as it
would be wired in a real deployment.

Run it directly: python3 end_to_end_orchestrator.py
"""

import sys
import os
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from observability.guardrails.guardrails import screen_input, validate_output, GuardrailAction
from observability.ai_gateway.model_gateway import (
    route_request, record_response, BudgetExceededError, ContentPolicyError,
)
from observability.human_in_the_loop.approval_gate import request_action, RiskTier, ApprovalStatus
from observability.orchestration.sub_agent_delegation import AgentScope, delegate, trace_delegation_chain


AGENT_IDENTITY = "svc-agent-semantic-layer"   # matches identity/identity_policy.yaml
AGENT_SCOPE = AgentScope(
    identity_name=AGENT_IDENTITY,
    permissions=frozenset({("gold", "semantic", "SELECT")}),
)

# A tiny stand-in for the real semantic layer this agent is scoped to -
# just enough governed metrics to make the walkthrough concrete. A real
# deployment resolves this against dbt/models/semantic/_metrics.yml,
# exactly as guardrails.py's validate_output() already does.
MOCK_SEMANTIC_LAYER = {
    "payment_leakage_rate": {"value": "3.2 percent", "period": "Q2 2026"},
    "denial_rate": {"value": "6.1 percent", "period": "Q2 2026"},
}


@dataclass
class HopLog:
    """One entry in the audit trail this run produces - mirrors the
    shape of mcp_audit_logger.py's ToolCallEvent closely enough to show
    how this run would actually be logged in a real deployment."""
    step: str
    status: str
    detail: str


class OrchestrationHalted(Exception):
    """Raised whenever any enforcement layer stops the request. This is
    the success case for that layer, not a bug - a halted run means a
    guardrail, budget, or approval gate did its job."""
    pass


def run_request(user_question: str, session_id: Optional[str] = None) -> dict:
    session_id = session_id or str(uuid.uuid4())
    trail: list[HopLog] = []

    def log(step, status, detail):
        trail.append(HopLog(step=step, status=status, detail=detail))
        print(f"[{step}] {status}: {detail}")

    print(f"\n{'='*70}\nNew request | session={session_id} | identity={AGENT_IDENTITY}\n{'='*70}")
    log("1. Identity", "tagged", f"Request tagged with agent identity '{AGENT_IDENTITY}' (ADR-013), not a human credential.")

    # --- 2. Guardrails: pre-call input screening -------------------------
    screen_result = screen_input(user_question)
    if screen_result.action == GuardrailAction.BLOCK:
        log("2. Guardrails (pre-call)", "BLOCKED", screen_result.reason)
        raise OrchestrationHalted(f"Halted at guardrails: {screen_result.reason}")
    elif screen_result.action == GuardrailAction.REDACT:
        log("2. Guardrails (pre-call)", "REDACTED", screen_result.reason)
        user_question = screen_result.processed_text
    else:
        log("2. Guardrails (pre-call)", "ALLOWED", screen_result.reason)

    # --- 3. AI Gateway: the model-leg call --------------------------------
    try:
        gw_request = route_request(
            feature="semantic-layer-qa",
            content=user_question,
            prompt_tokens=150,
            max_completion_tokens=250,
            preferred_provider="provider-a-small",
        )
        log("3. AI Gateway", "ALLOWED", f"Routed to {gw_request.provider}; budget and content policy cleared.")
    except (BudgetExceededError, ContentPolicyError) as e:
        log("3. AI Gateway", "REFUSED", str(e))
        raise OrchestrationHalted(f"Halted at AI Gateway: {e}")

    # --- Mocked reasoning step: the model decides which governed metric
    # this question resolves to. No real LLM call - this stands in for
    # the reasoning a real model call would perform.
    resolved_metric = _mock_resolve_metric(user_question)
    gw_response = record_response(gw_request, actual_completion_tokens=180,
                                   response_text=f"Resolved metric: {resolved_metric or 'no match'}")
    log("3. AI Gateway", "booked", f"Model call cost booked: {gw_response.cost_usd:.5f} dollars.")

    # --- 4. Orchestration: constrained delegation to a sub-agent ---------
    # This task is simple enough for the top-level agent alone, but we
    # demonstrate the delegation check anyway, exactly as a multi-step
    # task would use it - a lookup sub-task requesting no more than the
    # parent's own scope.
    sub_token = delegate(
        parent_scope=AGENT_SCOPE,
        requested_permissions=frozenset({("gold", "semantic", "SELECT")}),
        sub_agent_identity=f"{AGENT_IDENTITY}-subtask-lookup",
        task_description=f"Resolve and fetch: {resolved_metric or user_question}",
    )
    log("4. Orchestration", "delegated", f"Sub-agent '{sub_token.sub_agent_identity}' granted parent's own scope, nothing more.")

    # --- 5. MCP / semantic layer access check -----------------------------
    if resolved_metric is None:
        log("5. MCP / Semantic layer", "no-op", "No governed metric resolved; nothing to fetch.")
    else:
        log("5. MCP / Semantic layer", "ALLOWED",
            f"Tool call scoped to gold.semantic only (ADR-006); requesting '{resolved_metric}'.")

    # --- 6. Human-in-the-loop approval gate -------------------------------
    approval = request_action(
        action_description=f"Read-only semantic layer lookup: {resolved_metric or user_question}",
        requested_by=f"agent:{AGENT_IDENTITY}",
        risk_tier=RiskTier.TIER_1_READ_ONLY,
    )
    if approval.status == ApprovalStatus.PENDING:
        log("6. Human-in-the-loop", "PENDING", f"Halted pending human approval, request {approval.request_id}.")
        raise OrchestrationHalted("Halted at human-in-the-loop gate: awaiting approval.")
    log("6. Human-in-the-loop", approval.status.value, f"Tier 1 read-only lookup auto-approved, no human needed.")

    # --- 7. Governed query execution (represented, not live) -------------
    if resolved_metric and resolved_metric in MOCK_SEMANTIC_LAYER:
        result = MOCK_SEMANTIC_LAYER[resolved_metric]
        log("7. Query execution", "success",
            f"gold.semantic returned {resolved_metric} = {result['value']} for {result['period']} "
            f"(Unity Catalog row filters/column masks per ADR-007 apply automatically, not modeled here).")
    else:
        result = None
        log("7. Query execution", "no match", "No governed metric matched this question.")

    # --- 8. Guardrails: post-call output validation -----------------------
    validate_result = validate_output(resolved_metric=resolved_metric)
    if validate_result.action == GuardrailAction.BLOCK:
        log("8. Guardrails (post-call)", "BLOCKED", validate_result.reason)
        raise OrchestrationHalted(f"Halted at post-call guardrail: {validate_result.reason}")
    log("8. Guardrails (post-call)", "ALLOWED", validate_result.reason)

    # --- 9. Audit + cost logging ------------------------------------------
    log("9. Audit + cost logging", "recorded",
        f"Session {session_id} logged with identity, all {len(trail)} hops, and gateway cost "
        f"{gw_response.cost_usd:.5f} dollars (mirrors mcp_audit_logger.ToolCallEvent and "
        f"finops/agent_cost_tracker.py's per-feature rollup).")

    # --- 10. Summary ---------------------------------------------------
    if result:
        summary = f"{resolved_metric.replace('_', ' ').title()} for {result['period']} was {result['value']}."
    else:
        summary = "No governed metric matched this question; nothing was returned to avoid guessing."
    log("10. Summary", "returned", summary)

    return {
        "session_id": session_id,
        "summary": summary,
        "trail": [vars(h) for h in trail],
    }


def _mock_resolve_metric(user_question: str) -> Optional[str]:
    lowered = user_question.lower()
    if "payment leakage" in lowered or "leakage" in lowered:
        return "payment_leakage_rate"
    if "denial" in lowered:
        return "denial_rate"
    return None


if __name__ == "__main__":
    print(
        "Run simulate_end_to_end.py for a full demonstration: a normal "
        "successful request, a request halted by guardrails, and a "
        "higher-risk request halted pending human approval."
    )
