"""
simulate_agent_session.py

A runnable, dependency-free simulation of what mcp_audit_logger.py does
inside Databricks, for anyone reading this repo without a live Spark
session or workspace. It reimplements the same event schema and the
same three alert rules (error rate, repeated identical calls, latency
spike) against a plain Python list instead of a Delta table, so the
logic in mcp_audit_logger.py can be inspected and verified as real,
working code, not just described in prose.

Run it directly: python3 simulate_agent_session.py
It prints the simulated event log and any alerts the rules trigger.
"""

import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional


ERROR_RATE_THRESHOLD = 0.20
REPEATED_CALL_THRESHOLD = 5
LATENCY_P99_THRESHOLD_MS = 5000


@dataclass
class ToolCallEvent:
    event_id: str
    timestamp_utc: str
    session_id: str
    caller_identity: str
    user_question: str
    tool_name: str
    tool_arguments: str
    resolved_metric: Optional[str]
    matched_synonym: Optional[str]
    status: str
    error_message: Optional[str]
    latency_ms: int
    row_count_returned: Optional[int]


def make_event(session_id, question, tool_name, tool_args, resolved_metric,
               synonym, status, latency_ms, error_message=None, rows=None):
    return ToolCallEvent(
        event_id=str(uuid.uuid4()),
        timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        session_id=session_id,
        caller_identity="agent:claude-desktop/rizwan",
        user_question=question,
        tool_name=tool_name,
        tool_arguments=json.dumps(tool_args),
        resolved_metric=resolved_metric,
        matched_synonym=synonym,
        status=status,
        error_message=error_message,
        latency_ms=latency_ms,
        row_count_returned=rows,
    )


def evaluate_alert_rules(events: list[ToolCallEvent]) -> list[dict]:
    """The exact same three rules as check_for_agent_anomalies() in
    mcp_audit_logger.py, reimplemented over a plain Python list instead
    of a Spark DataFrame, so the logic is checkable without Spark."""
    triggered = []
    total = len(events)
    if total == 0:
        return triggered

    error_count = sum(1 for e in events if e.status == "error")
    error_rate = error_count / total
    if error_rate > ERROR_RATE_THRESHOLD:
        triggered.append({
            "rule": "high_error_rate",
            "severity": "P1",
            "detail": f"Error rate {error_rate:.0%} ({error_count}/{total} calls failed).",
        })

    call_counts = {}
    for e in events:
        key = (e.tool_name, e.tool_arguments)
        call_counts[key] = call_counts.get(key, 0) + 1
    for (tool_name, args), count in call_counts.items():
        if count >= REPEATED_CALL_THRESHOLD:
            triggered.append({
                "rule": "repeated_identical_calls",
                "severity": "P2",
                "detail": f"Tool '{tool_name}' called with identical arguments {count} times - possible stuck loop.",
            })

    latencies = sorted(e.latency_ms for e in events)
    if latencies:
        p99_index = min(len(latencies) - 1, int(len(latencies) * 0.99))
        p99 = latencies[p99_index]
        if p99 > LATENCY_P99_THRESHOLD_MS:
            triggered.append({
                "rule": "latency_spike",
                "severity": "P2",
                "detail": f"p99 latency {p99} ms exceeds {LATENCY_P99_THRESHOLD_MS} ms threshold.",
            })

    return triggered


def scenario_healthy_session() -> list[ToolCallEvent]:
    session = str(uuid.uuid4())
    return [
        make_event(session, "What's our risk score trend looking like this year?",
                   "list_metrics", {"search": "risk score"}, None,
                   "risk score -> yoy_raf_score_trend", "success", 142, rows=1),
        make_event(session, "What's our risk score trend looking like this year?",
                   "query_metrics", {"metrics": ["yoy_raf_score_trend"], "group_by": ["metric_time"]},
                   "yoy_raf_score_trend", "risk score -> yoy_raf_score_trend", "success", 487, rows=12),
        make_event(session, "What was our medical loss ratio last quarter?",
                   "list_metrics", {"search": "medical loss ratio"}, None, None, "error", 98,
                   error_message="No matching metric found - Medical Loss Ratio is a documented Data Gap.", rows=0),
    ]


def scenario_agent_stuck_in_a_loop() -> list[ToolCallEvent]:
    """Simulates the exact failure mode ADR-008 calls out: an agent
    retrying the same failing query rather than backing off, which a
    passive log would only reveal after the fact - this is the scenario
    the repeated_identical_calls and high_error_rate rules exist to
    catch while it's still happening."""
    session = str(uuid.uuid4())
    events = []
    for _ in range(8):
        events.append(make_event(
            session, "What's the net VBC contract value by region?",
            "query_metrics", {"metrics": ["net_vbc_contract_value"], "group_by": ["region"]},
            None, None, "error", 6200,
            error_message="Metric 'net_vbc_contract_value' not found - out of scope, requires plan/employer_group data not yet modeled.",
        ))
    return events


if __name__ == "__main__":
    print("=== Scenario 1: healthy agent session ===")
    healthy = scenario_healthy_session()
    for e in healthy:
        print(json.dumps(asdict(e)))
    alerts = evaluate_alert_rules(healthy)
    print(f"Alerts triggered: {len(alerts)}\n")

    print("=== Scenario 2: agent stuck retrying a nonexistent metric ===")
    stuck = scenario_agent_stuck_in_a_loop()
    for e in stuck:
        print(json.dumps(asdict(e)))
    alerts = evaluate_alert_rules(stuck)
    print(f"Alerts triggered: {len(alerts)}")
    for a in alerts:
        print(f"  [{a['severity']}] {a['rule']}: {a['detail']}")
