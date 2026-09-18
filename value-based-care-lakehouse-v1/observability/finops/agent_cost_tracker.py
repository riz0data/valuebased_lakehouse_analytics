"""
agent_cost_tracker.py

Reference implementation for AI/agent cost attribution - the second
half of the FinOps layer, alongside lakehouse_cost_attribution.sql.

Mechanism, in plain terms:

  Databricks system tables (system.billing.usage) have no visibility
  into LLM API cost, since a model call to an external provider is not
  Databricks compute - it never shows up in a DBU bill. So agent cost
  has to be captured at the point of the call itself, not read after
  the fact from a billing table the way lakehouse compute cost is.

  The real, current industry pattern (see ADR-011 in
  docs/decisions/ADRs.md for the sources) is call-level attribution:
  every LLM call is tagged with metadata (session, feature, user) at
  call time, its token usage is read directly from the provider's own
  response (every major provider returns prompt/completion token
  counts), and cost is derived as tokens x a published per-token rate
  looked up by model name.

  This project already logs every agent tool call via
  observability/mcp_audit_logger.py's ToolCallEvent. Rather than
  building a separate logging pipeline, this module extends that same
  event with cost fields, so cost attribution rides on the audit log
  this project already has, instead of a second bolted-on system.

Honest limitation, stated up front: token cost is only part of the
real cost picture in agentic workloads. A single user question can
trigger many tool calls, retries, and a wide context window, so the
real cost driver is calls-per-task, not tokens-per-call alone. This
module tracks token cost accurately; it does not attempt to model
retry or orchestration overhead, which a real deployment would want to
track as its own metric (see README.md in this folder).

Not a running service - there is no live agent deployed against this
portfolio project. Every function here is written to be dropped into a
real Databricks Job or MCP proxy as-is.
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, timezone

from pyspark.sql import SparkSession, Row
from pyspark.sql import functions as F

CATALOG = "gold"
SCHEMA = "observability"
COST_TABLE = f"{CATALOG}.{SCHEMA}.agent_cost_log"

# Published per-token rates, in dollars, per model. Kept as an explicit
# lookup table rather than hardcoded into the cost formula, since rates
# change and differ by provider - this table is the one thing a real
# deployment would need to keep current by hand or via provider API.
# Rates below are illustrative placeholders for this reference
# implementation, not live pricing - see README.md for how to source
# current rates before using this against a real bill.
MODEL_RATES_PER_1K_TOKENS = {
    "claude-sonnet-5":   {"input": 0.003, "output": 0.015},
    "claude-haiku-5":    {"input": 0.0008, "output": 0.004},
}


@dataclass
class AgentCostEvent:
    event_id: str                  # matches the ToolCallEvent.event_id it extends
    timestamp_utc: str
    session_id: str
    caller_identity: str
    feature_tag: str               # which feature/workflow triggered this call
    model_name: str
    input_tokens: int
    output_tokens: int
    cost_dollars: float


def compute_call_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Reads token counts directly from the provider's own response object
    in a real deployment (every major provider returns prompt/completion
    token counts on each call) and converts to dollars using the
    published rate for that model. Raises on an unknown model rather
    than silently returning zero, since a silent zero-cost call is
    exactly the kind of drift a real FinOps review would want caught
    immediately, not discovered a month later.
    """
    if model_name not in MODEL_RATES_PER_1K_TOKENS:
        raise ValueError(
            f"No published rate on file for model '{model_name}' - "
            f"add it to MODEL_RATES_PER_1K_TOKENS before tracking cost "
            f"for this model, rather than letting it pass as free."
        )
    rates = MODEL_RATES_PER_1K_TOKENS[model_name]
    cost = (input_tokens / 1000) * rates["input"] + (output_tokens / 1000) * rates["output"]
    return round(cost, 6)


_COST_EVENT_BUFFER: list[AgentCostEvent] = []


def record_cost_event(event: AgentCostEvent) -> None:
    """
    Called immediately after each agent tool call completes, alongside
    mcp_audit_logger.record_event() for the same call - same event_id,
    so the two logs join cleanly for a combined behavior-plus-cost view.
    """
    _COST_EVENT_BUFFER.append(event)


def log_agent_cost_batch(spark: SparkSession) -> int:
    """
    Runs on the same 1-minute schedule as
    mcp_audit_logger.log_agent_activity_batch(), as a sibling Databricks
    Job step. Drains the cost event buffer and appends to the Delta
    cost log table. Returns the number of events written.
    """
    global _COST_EVENT_BUFFER
    batch, _COST_EVENT_BUFFER = _COST_EVENT_BUFFER, []

    if not batch:
        return 0

    rows = [Row(**asdict(e)) for e in batch]
    df = spark.createDataFrame(rows)

    (
        df.write
        .format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(COST_TABLE)
    )
    return len(batch)


def daily_cost_by_feature(spark: SparkSession, days: int = 30):
    """
    The chargeback query a FinOps review actually wants for the agent
    side: real dollar spend per feature per day, mirroring the
    per-project attribution lakehouse_cost_attribution.sql produces for
    compute. Joins nothing external - every field it groups by was
    attached at call time.
    """
    return (
        spark.table(COST_TABLE)
        .where(F.col("timestamp_utc") >= F.expr(f"current_timestamp() - INTERVAL {days} DAYS"))
        .groupBy(F.to_date("timestamp_utc").alias("usage_date"), "feature_tag", "model_name")
        .agg(
            F.sum("input_tokens").alias("total_input_tokens"),
            F.sum("output_tokens").alias("total_output_tokens"),
            F.round(F.sum("cost_dollars"), 2).alias("total_cost_dollars"),
        )
        .orderBy(F.desc("usage_date"), F.desc("total_cost_dollars"))
    )


if __name__ == "__main__":
    print(
        "This module defines Databricks Job task functions - "
        "log_agent_cost_batch() and daily_cost_by_feature() - meant to "
        "run alongside mcp_audit_logger.py's functions on the same "
        "1-minute schedule inside a Databricks workspace with a live "
        "SparkSession. It is not meant to be run standalone outside "
        "Databricks. See observability/finops/README.md for the Job "
        "configuration this maps to, and "
        "example_agent_cost_output.txt for a runnable, local "
        "demonstration that produces example output without requiring "
        "Spark or Databricks."
    )
