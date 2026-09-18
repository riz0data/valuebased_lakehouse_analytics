"""
simulate_agent_cost.py

A runnable, dependency-free simulation of what agent_cost_tracker.py
does inside Databricks, for anyone reading this repo without a live
Spark session or workspace. It reimplements the same cost event schema
and the same daily-cost-by-feature rollup against a plain Python list
instead of a Delta table, so the cost logic can be inspected and
verified as real, working code, not just described in prose.

Run it directly: python3 simulate_agent_cost.py
It prints a simulated day of agent tool calls, their token counts and
computed dollar cost, and the resulting cost-by-feature rollup.
"""

import json
import time
import uuid
from dataclasses import dataclass, asdict
from collections import defaultdict


MODEL_RATES_PER_1K_TOKENS = {
    "claude-sonnet-5": {"input": 0.003, "output": 0.015},
    "claude-haiku-5":  {"input": 0.0008, "output": 0.004},
}


@dataclass
class AgentCostEvent:
    event_id: str
    timestamp_utc: str
    session_id: str
    caller_identity: str
    feature_tag: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost_dollars: float


def compute_call_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Same logic as agent_cost_tracker.compute_call_cost() - tokens
    read from the (simulated, here) provider response, multiplied by
    the published per-token rate for that model."""
    if model_name not in MODEL_RATES_PER_1K_TOKENS:
        raise ValueError(f"No published rate on file for model '{model_name}'")
    rates = MODEL_RATES_PER_1K_TOKENS[model_name]
    cost = (input_tokens / 1000) * rates["input"] + (output_tokens / 1000) * rates["output"]
    return round(cost, 6)


def make_event(session_id, feature_tag, model_name, input_tokens, output_tokens):
    return AgentCostEvent(
        event_id=str(uuid.uuid4()),
        timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        session_id=session_id,
        caller_identity="agent:claude-desktop/rizwan",
        feature_tag=feature_tag,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_dollars=compute_call_cost(model_name, input_tokens, output_tokens),
    )


def daily_cost_by_feature(events: list[AgentCostEvent]) -> list[dict]:
    """Same rollup as agent_cost_tracker.daily_cost_by_feature(), over
    a plain Python list instead of a Spark DataFrame."""
    rollup = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cost_dollars": 0.0})
    for e in events:
        key = (e.feature_tag, e.model_name)
        rollup[key]["input_tokens"] += e.input_tokens
        rollup[key]["output_tokens"] += e.output_tokens
        rollup[key]["cost_dollars"] += e.cost_dollars

    result = []
    for (feature_tag, model_name), totals in rollup.items():
        result.append({
            "feature_tag": feature_tag,
            "model_name": model_name,
            "total_input_tokens": totals["input_tokens"],
            "total_output_tokens": totals["output_tokens"],
            "total_cost_dollars": round(totals["cost_dollars"], 4),
        })
    return sorted(result, key=lambda r: r["total_cost_dollars"], reverse=True)


def run_simulation():
    session_id = str(uuid.uuid4())

    # A simulated day's worth of agent calls across a few features -
    # realistic token counts for semantic-layer metric lookups (small
    # inputs, larger outputs when an agent explains a result).
    scenarios = [
        ("metric_lookup",      "claude-sonnet-5", 420,  180),
        ("metric_lookup",      "claude-sonnet-5", 380,  150),
        ("metric_lookup",      "claude-haiku-5",  410,  140),
        ("nl_to_metric_query", "claude-sonnet-5", 950,  420),
        ("nl_to_metric_query", "claude-sonnet-5", 1100, 510),
        ("governance_qna",     "claude-sonnet-5", 1800, 900),
        ("governance_qna",     "claude-haiku-5",  1650, 800),
        ("metric_lookup",      "claude-sonnet-5", 400,  160),
        ("nl_to_metric_query", "claude-haiku-5",  980,  400),
        ("governance_qna",     "claude-sonnet-5", 2100, 1050),
    ]

    events = [make_event(session_id, feature, model, in_tok, out_tok)
              for feature, model, in_tok, out_tok in scenarios]

    print(f"Simulated session: {session_id}")
    print(f"Total agent calls logged: {len(events)}\n")

    print("Per-call cost detail:")
    for e in events:
        print(
            f"  [{e.feature_tag:<18}] {e.model_name:<16} "
            f"in={e.input_tokens:>5} out={e.output_tokens:>5} "
            f"cost=${e.cost_dollars:.6f}"
        )

    total_cost = sum(e.cost_dollars for e in events)
    print(f"\nTotal simulated spend across all calls: ${total_cost:.4f}\n")

    print("Daily cost by feature (chargeback view):")
    rollup = daily_cost_by_feature(events)
    for r in rollup:
        print(
            f"  {r['feature_tag']:<18} {r['model_name']:<16} "
            f"in_tokens={r['total_input_tokens']:>6} "
            f"out_tokens={r['total_output_tokens']:>6} "
            f"cost=${r['total_cost_dollars']:.4f}"
        )


if __name__ == "__main__":
    run_simulation()
