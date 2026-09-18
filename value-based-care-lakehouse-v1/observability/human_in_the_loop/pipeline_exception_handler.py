"""
pipeline_exception_handler.py

The human-in-the-loop and exception-handling layer for the lakehouse
pipeline side of this project - dbt runs and Data Vault loads - as
opposed to approval_gate.py, which covers the agent/AI side. Both route
through the same centralized notification_config.py, so a pipeline
failure and an agent approval request land in the same inbox, at the
same single configurable address.

Design principle: not every pipeline failure needs a human, the same
risk-tiering logic as the agent side applies here too. A single row
failing a not-null test on a staging model is routine and should be
logged, not paged. A load failure on a Hub or Link table in the Data
Vault layer, or a dbt test failure on a Gold-layer semantic model that
agents query directly, is a different matter - that can propagate bad
numbers straight to a governed metric an agent might then confidently
report, so it escalates to a human rather than just being logged.

This is written as a wrapper around dbt invocation and Data Vault load
steps, not a replacement for dbt's own test framework - it reads dbt's
own run results and test results (run_results.json, the same artifact
dbt already produces) and decides, per failure, whether this is a
log-and-continue case or a stop-and-notify-a-human case.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from observability.human_in_the_loop.notification_config import NOTIFY_EMAIL


class FailureSeverity(Enum):
    LOW = "low"        # e.g. a handful of rows failing a staging-layer test
    MEDIUM = "medium"  # e.g. a Data Vault satellite load partially failing
    HIGH = "high"      # e.g. a Hub/Link load failure, or a Gold-layer model
                        # test failure - anything that can reach an agent-
                        # queryable metric with bad or missing data


# Which dbt model layers, if a test fails there, are automatically HIGH
# severity regardless of the test type - because that layer is what
# agents actually query (see ADR-006), so a silent bad number there is
# a governance problem, not just a data quality one.
AGENT_FACING_LAYERS = ("gold", "semantic")


@dataclass
class PipelineException:
    exception_id: str
    timestamp_utc: str
    pipeline_name: str          # e.g. "dbt_run", "vault_hub_load"
    model_or_table: str
    failure_type: str           # e.g. "test_failure", "load_error"
    severity: FailureSeverity
    detail: str
    notify_email: Optional[str]
    human_notified: bool


_EXCEPTION_LOG: list[PipelineException] = []


def classify_severity(model_or_table: str, failure_type: str) -> FailureSeverity:
    """
    The actual tiering logic. Deliberately simple and explicit - same
    philosophy as mcp_audit_logger.py's fixed alert thresholds: anyone
    reading this can see exactly why a failure was or wasn't escalated,
    rather than trusting an opaque scoring model.
    """
    layer = model_or_table.split(".")[0] if "." in model_or_table else ""

    if failure_type == "load_error":
        # Any load failure (not just a test) in the Vault or Gold layer
        # means data is missing or stale downstream - always HIGH.
        return FailureSeverity.HIGH

    if layer in AGENT_FACING_LAYERS:
        return FailureSeverity.HIGH

    if layer == "vault":
        return FailureSeverity.MEDIUM

    return FailureSeverity.LOW


def handle_pipeline_exception(pipeline_name: str, model_or_table: str,
                               failure_type: str, detail: str) -> PipelineException:
    """
    The single entry point every dbt run and Data Vault load wrapper in
    this project calls when something fails. Classifies severity, logs
    it, and - for MEDIUM and HIGH only - notifies a human at the one
    centralized address. LOW severity is logged for review but does not
    interrupt anyone, on purpose, to keep the notification signal
    meaningful (the same rubber-stamping risk noted in approval_gate.py
    applies here: page a human for everything and they stop reading).
    """
    severity = classify_severity(model_or_table, failure_type)
    should_notify = severity in (FailureSeverity.MEDIUM, FailureSeverity.HIGH)

    exc = PipelineException(
        exception_id=str(uuid.uuid4()),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        pipeline_name=pipeline_name,
        model_or_table=model_or_table,
        failure_type=failure_type,
        severity=severity,
        detail=detail,
        notify_email=NOTIFY_EMAIL if should_notify else None,
        human_notified=should_notify,
    )

    _EXCEPTION_LOG.append(exc)

    if should_notify:
        _send_exception_notification(exc)

    return exc


def _send_exception_notification(exc: PipelineException) -> None:
    """
    Same centralized-destination principle as
    approval_gate._send_approval_notification() - this is the one
    function that constructs a pipeline exception alert, and it always
    routes through NOTIFY_EMAIL from notification_config.py.
    """
    urgency = "URGENT - " if exc.severity == FailureSeverity.HIGH else ""
    print(
        f"[PIPELINE EXCEPTION - {urgency}{exc.severity.value}] "
        f"To: {exc.notify_email} | "
        f"Pipeline: {exc.pipeline_name} | Target: {exc.model_or_table} | "
        f"{exc.failure_type}: {exc.detail} | Exception ID: {exc.exception_id}"
    )


def parse_dbt_run_results(run_results_json_path: str, pipeline_name: str = "dbt_run") -> list[PipelineException]:
    """
    Reads dbt's own run_results.json (the real artifact dbt produces
    after every `dbt run` or `dbt test` - no custom parsing format
    invented here) and routes every failed node through
    handle_pipeline_exception(). This is the real integration point: a
    CI job or Databricks Job step calls this immediately after `dbt
    build`, rather than this project reimplementing dbt's own test
    execution.
    """
    with open(run_results_json_path) as f:
        results = json.load(f)

    exceptions = []
    for result in results.get("results", []):
        if result.get("status") in ("fail", "error"):
            unique_id = result.get("unique_id", "unknown_model")
            failure_type = "test_failure" if ".test." in unique_id else "load_error"
            exceptions.append(
                handle_pipeline_exception(
                    pipeline_name=pipeline_name,
                    model_or_table=unique_id,
                    failure_type=failure_type,
                    detail=result.get("message") or f"status={result.get('status')}",
                )
            )
    return exceptions


if __name__ == "__main__":
    print(
        "This module defines the human-in-the-loop exception-handling "
        "layer for pipeline failures (dbt runs, Data Vault loads). Run "
        "simulate_pipeline_exceptions.py for a runnable, dependency-free "
        "demonstration across LOW, MEDIUM, and HIGH severity failures."
    )
