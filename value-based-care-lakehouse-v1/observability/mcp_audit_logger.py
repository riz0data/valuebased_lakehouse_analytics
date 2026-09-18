"""
mcp_audit_logger.py

Continuous audit logging for agent activity against this project's
dbt-mcp server, writing to a Delta table on a one-minute cadence, plus a
companion alerting job that reads that table and flags misbehavior.

This is a reference implementation, not a running service - there is no
live agent deployed against this portfolio project. Every piece here is
written to be dropped into a real Databricks Job as-is; see
observability/README.md and ADR-008 in docs/decisions/ADRs.md for the
full design reasoning, including why this is a scheduled micro-batch
job rather than a true low-latency stream.

Two Databricks Jobs, working together:

  1. log_agent_activity_batch()  - runs every 1 minute. Buffers agent
     tool-call events in-process during the interval (in a real deploy,
     this would be events an MCP proxy forwards to this job's queue),
     then appends that minute's batch to a Delta table.

  2. check_for_agent_anomalies() - runs every 1 minute, just after the
     logger, reading the same Delta table's most recent window and
     evaluating simple rules (error rate, repeated identical calls,
     token/cost spikes). If a rule trips, it sends an alert.

Both are plain PySpark/Python functions with no invented Databricks
APIs - only functions and syntax that are real, current, documented
Databricks/PySpark mechanisms (see the ADR for citations).
"""

import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

from pyspark.sql import SparkSession, Row
from pyspark.sql import functions as F

CATALOG = "gold"
SCHEMA = "observability"
LOG_TABLE = f"{CATALOG}.{SCHEMA}.agent_query_log"
ALERT_TABLE = f"{CATALOG}.{SCHEMA}.agent_alerts"

# Thresholds an alert run evaluates against the last window of activity.
# Deliberately simple, explicit numbers rather than a learned anomaly
# model - see ADR-008 for why that trade-off makes sense at this scale.
ERROR_RATE_THRESHOLD = 0.20        # alert if >20% of calls failed in the window
REPEATED_CALL_THRESHOLD = 5        # alert if the same tool+args repeats 5+ times in the window
LATENCY_P99_THRESHOLD_MS = 5000    # alert if p99 latency exceeds 5 seconds


@dataclass
class ToolCallEvent:
    event_id: str
    timestamp_utc: str
    session_id: str
    caller_identity: str
    user_question: str
    tool_name: str
    tool_arguments: str          # stored as a JSON string for a simple Delta schema
    resolved_metric: Optional[str]
    matched_synonym: Optional[str]
    status: str                  # "success" | "error" | "denied"
    error_message: Optional[str]
    latency_ms: int
    row_count_returned: Optional[int]


# In a real MCP proxy, this in-memory buffer would be appended to on
# every intercepted tool call, and drained each time the 1-minute batch
# job runs. It is module-level here only to keep this file runnable and
# self-contained as a reference implementation.
_EVENT_BUFFER: list[ToolCallEvent] = []


def record_event(event: ToolCallEvent) -> None:
    """
    Called by the MCP proxy immediately after each tool call completes.
    Cheap and synchronous on purpose - it just appends to the in-memory
    buffer; the actual Delta write happens on the 1-minute batch cycle
    below, not on every call, so logging never adds latency to the
    agent's own tool calls.
    """
    _EVENT_BUFFER.append(event)


def log_agent_activity_batch(spark: SparkSession) -> int:
    """
    Runs every 1 minute as a scheduled Databricks Job. Drains whatever
    tool-call events have buffered since the last run and appends them
    to the Delta audit log table. Returns the number of events written.

    Uses a plain `.write.format("delta").mode("append")` batch write on
    a schedule, rather than Structured Streaming, since 1-minute
    freshness is a lenient-latency use case Databricks explicitly
    recommends handling with a scheduled batch job instead of a
    continuously-running stream.
    """
    global _EVENT_BUFFER
    batch, _EVENT_BUFFER = _EVENT_BUFFER, []

    if not batch:
        return 0

    rows = [Row(**asdict(e)) for e in batch]
    df = spark.createDataFrame(rows)

    (
        df.write
        .format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(LOG_TABLE)
    )
    return len(batch)


def check_for_agent_anomalies(spark: SparkSession, window_minutes: int = 1) -> list[dict]:
    """
    Runs every 1 minute, immediately after log_agent_activity_batch, as
    a second scheduled Databricks Job step. Reads the most recent
    window of the Delta audit log and evaluates it against the simple
    rules above. Any rule that trips gets written to ALERT_TABLE and
    returned, so a downstream step (email, Slack webhook, PagerDuty)
    can act on it - see send_alert() below for the simplest version of
    that, a Databricks SQL alert-style email.
    """
    recent = (
        spark.table(LOG_TABLE)
        .where(F.col("timestamp_utc") >= F.expr(f"current_timestamp() - INTERVAL {window_minutes} MINUTES"))
    )

    total_calls = recent.count()
    if total_calls == 0:
        return []

    triggered = []

    # Rule 1: error rate
    error_count = recent.where(F.col("status") == "error").count()
    error_rate = error_count / total_calls
    if error_rate > ERROR_RATE_THRESHOLD:
        triggered.append({
            "rule": "high_error_rate",
            "severity": "P1",
            "detail": f"Error rate {error_rate:.0%} over last {window_minutes} min ({error_count}/{total_calls} calls failed).",
        })

    # Rule 2: the same tool+arguments repeating suspiciously often -
    # often a sign of a stuck loop or an agent retrying the same wrong
    # query rather than backing off.
    repeats = (
        recent.groupBy("tool_name", "tool_arguments")
        .count()
        .where(F.col("count") >= REPEATED_CALL_THRESHOLD)
        .collect()
    )
    for r in repeats:
        triggered.append({
            "rule": "repeated_identical_calls",
            "severity": "P2",
            "detail": f"Tool '{r['tool_name']}' called with identical arguments {r['count']} times in {window_minutes} min - possible stuck loop.",
        })

    # Rule 3: latency spike (p99 over threshold)
    p99 = recent.approxQuantile("latency_ms", [0.99], 0.01)
    if p99 and p99[0] > LATENCY_P99_THRESHOLD_MS:
        triggered.append({
            "rule": "latency_spike",
            "severity": "P2",
            "detail": f"p99 latency {p99[0]:.0f} ms over last {window_minutes} min, exceeds {LATENCY_P99_THRESHOLD_MS} ms threshold.",
        })

    if triggered:
        alert_rows = [
            Row(
                alert_id=str(uuid.uuid4()),
                triggered_at_utc=datetime.now(timezone.utc).isoformat(),
                rule=t["rule"],
                severity=t["severity"],
                detail=t["detail"],
            )
            for t in triggered
        ]
        spark.createDataFrame(alert_rows).write.format("delta").mode("append").saveAsTable(ALERT_TABLE)
        for t in triggered:
            send_alert(t)

    return triggered


def send_alert(alert: dict) -> None:
    """
    Simplest real notification path: Databricks SQL Alerts (or a
    Databricks Jobs task's own email/webhook notification setting) can
    already email or Slack-webhook a team the moment a row lands in
    ALERT_TABLE, with zero custom code - point a Databricks SQL Alert at
    `SELECT * FROM gold.observability.agent_alerts WHERE triggered_at_utc
    > current_timestamp() - INTERVAL 2 MINUTES` on the same schedule.
    This function is a stand-in for that, or for a custom webhook call,
    kept here only so this reference implementation is runnable
    end-to-end without requiring a configured SQL Alert.
    """
    print(f"[ALERT - {alert['severity']}] {alert['rule']}: {alert['detail']}")


if __name__ == "__main__":
    print(
        "This module defines Databricks Job task functions - "
        "log_agent_activity_batch() and check_for_agent_anomalies() - "
        "meant to run on a 1-minute schedule inside a Databricks "
        "workspace with a live SparkSession. It is not meant to be run "
        "standalone outside Databricks. See observability/README.md "
        "for the Job configuration this maps to, and "
        "observability/simulate_agent_session.py for a runnable, "
        "local demonstration that produces example output without "
        "requiring Spark or Databricks."
    )
