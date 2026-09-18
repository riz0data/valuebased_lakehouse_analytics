"""
evaluate_agent.py

A three-layer evaluation harness for AI agent responses against this
project's governed metrics, following the layered pattern used across
the industry (deterministic checks, golden-dataset regression testing,
and judge-based scoring), rather than relying on a single method - see
ADR-009 in docs/decisions/ADRs.md for the full reasoning behind this
design and why a single golden-dataset check isn't considered
sufficient on its own.

Like the rest of observability/, there is no live agent deployed
against this project - this harness is runnable today against a
simulated "agent" (a simple rule-based stand-in that mimics correct and
incorrect metric resolution), so the evaluation logic itself is real,
tested code, ready to be pointed at a real agent's output the moment
one exists.

Layer 1 - Deterministic checks (near-zero cost, run on every response):
    Schema and format validation - is the response even structured
    correctly? Does it reference a metric that actually exists in
    _metrics.yml? No LLM judge needed for this layer - these are the
    catches that are "free" and should never depend on model-based
    scoring at all.

Layer 2 - Golden dataset regression testing (run on every metric change):
    A fixed set of questions with known-correct expected metrics,
    generated directly from the synonyms already defined in
    _metrics.yml (see golden_dataset.json). Exact-match: did the agent
    resolve to the expected metric, yes or no.

Layer 3 - Judge-style rubric scoring (sampled, higher cost):
    For cases that pass Layer 1 and 2, or for open-ended questions with
    no single correct metric, a rubric-based score checks softer
    qualities: did the agent's chosen metric actually match the
    domain implied by the question, did it avoid overconfidently
    answering when no metric applies. This reference implementation
    uses an explicit, deterministic rubric function rather than a real
    frontier-model judge call, so it is runnable with no API key or
    network access - see ADR-009 for how this would be swapped for a
    real LLM-as-judge call in production.
"""

import json
import yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_YML = REPO_ROOT / "dbt" / "models" / "semantic" / "_metrics.yml"
GOLDEN_DATASET = Path(__file__).resolve().parent / "golden_dataset.json"


def load_metrics() -> dict:
    with open(METRICS_YML) as f:
        data = yaml.safe_load(f)
    return {m["name"]: m for m in data.get("metrics", [])}


def load_golden_dataset() -> list[dict]:
    with open(GOLDEN_DATASET) as f:
        return json.load(f)


@dataclass
class EvalResult:
    case_id: str
    question: str
    expected_metric: Optional[str]
    actual_metric: Optional[str]
    layer1_schema_valid: bool
    layer2_exact_match: Optional[bool]   # None when there's no single expected metric to match
    layer3_rubric_score: float           # 0.0 to 1.0
    layer3_rubric_notes: str
    passed: bool


def simulated_agent_resolve(question: str, metrics: dict) -> Optional[str]:
    """
    Stand-in for a real agent's metric-resolution step, used only so
    this harness is runnable end to end without a live agent. Mimics
    the real behavior being tested: match the question against each
    metric's meta.synonyms, case-insensitively substring-matched.
    A real deployment would replace this one function with an actual
    call to the deployed agent (or to dbt-mcp's list_metrics/
    query_metrics directly) and leave every evaluation layer below
    unchanged.
    """
    q = question.lower()
    best_match = None
    best_match_len = 0
    for name, m in metrics.items():
        for syn in m.get("meta", {}).get("synonyms", []):
            if syn.lower() in q and len(syn) > best_match_len:
                best_match = name
                best_match_len = len(syn)
    return best_match


# ---------------------------------------------------------------------
# Layer 1: deterministic checks
# ---------------------------------------------------------------------

def layer1_schema_check(actual_metric: Optional[str], metrics: dict) -> bool:
    """Near-zero-cost check: if the agent claims a metric, does that
    metric actually exist in _metrics.yml? Catches hallucinated metric
    names before any expensive scoring runs at all."""
    if actual_metric is None:
        return True  # "no match" is a valid, schema-correct response
    return actual_metric in metrics


# ---------------------------------------------------------------------
# Layer 2: golden dataset exact match
# ---------------------------------------------------------------------

def layer2_exact_match(expected_metric: Optional[str], actual_metric: Optional[str]) -> bool:
    return expected_metric == actual_metric


# ---------------------------------------------------------------------
# Layer 3: rubric-based scoring (deterministic stand-in for LLM-as-judge)
# ---------------------------------------------------------------------

def layer3_rubric_score(case: dict, actual_metric: Optional[str], metrics: dict) -> tuple[float, str]:
    """
    A real deployment swaps this function for a frontier-model judge
    call: give the judge the question, the agent's chosen metric (and
    its description), and a rubric, then ask it to score domain
    relevance and confidence-calibration on a 0 to 1 scale. This
    reference version implements the same rubric deterministically -
    same inputs and outputs, no model call - specifically so the
    harness is runnable without an API key while keeping the interface
    a real judge call would slot into unchanged.

    Rubric:
      1.0 - correct metric, or correctly returned no match when none applies
      0.5 - wrong metric, but same domain as expected (a "close miss")
      0.0 - wrong metric in a different domain, or confidently answered
            when it should have returned no match
    """
    expected_metric = case.get("expected_metric")
    expected_domain = case.get("expected_domain")

    if expected_metric is None:
        if actual_metric is None:
            return 1.0, "Correctly returned no match for a question with no governed metric."
        return 0.0, f"Should have returned no match, but confidently resolved to '{actual_metric}' instead."

    if actual_metric == expected_metric:
        return 1.0, "Resolved to the correct governed metric."

    if actual_metric is None:
        return 0.0, f"Failed to resolve any metric; expected '{expected_metric}'."

    actual_domain = metrics.get(actual_metric, {}).get("meta", {}).get("domain")
    if actual_domain == expected_domain:
        return 0.5, (
            f"Resolved to '{actual_metric}' (same domain '{actual_domain}' as expected "
            f"'{expected_metric}') - a close miss, not a random guess."
        )
    return 0.0, (
        f"Resolved to '{actual_metric}' (domain '{actual_domain}'), completely unrelated "
        f"to the expected '{expected_metric}' (domain '{expected_domain}')."
    )


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------

def run_evaluation() -> list[EvalResult]:
    metrics = load_metrics()
    cases = load_golden_dataset()
    results = []

    for case in cases:
        actual_metric = simulated_agent_resolve(case["question"], metrics)

        schema_ok = layer1_schema_check(actual_metric, metrics)
        exact_match = layer2_exact_match(case.get("expected_metric"), actual_metric)
        rubric_score, rubric_notes = layer3_rubric_score(case, actual_metric, metrics)

        passed = schema_ok and exact_match and rubric_score == 1.0

        results.append(EvalResult(
            case_id=case["case_id"],
            question=case["question"],
            expected_metric=case.get("expected_metric"),
            actual_metric=actual_metric,
            layer1_schema_valid=schema_ok,
            layer2_exact_match=exact_match,
            layer3_rubric_score=rubric_score,
            layer3_rubric_notes=rubric_notes,
            passed=passed,
        ))

    return results


def summarize(results: list[EvalResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_rubric = sum(r.layer3_rubric_score for r in results) / total if total else 0.0
    failures = [r for r in results if not r.passed]
    return {
        "total_cases": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "average_rubric_score": avg_rubric,
        "failures": [asdict(r) for r in failures],
    }


if __name__ == "__main__":
    results = run_evaluation()
    summary = summarize(results)

    print(f"Ran {summary['total_cases']} golden test cases against the simulated agent.\n")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case_id}: expected={r.expected_metric!r} actual={r.actual_metric!r} rubric={r.layer3_rubric_score}")
        if not r.passed:
            print(f"       -> {r.layer3_rubric_notes}")

    print(f"\nPass rate: {summary['pass_rate']:.0%} ({summary['passed']}/{summary['total_cases']})")
    print(f"Average rubric score: {summary['average_rubric_score']:.2f}")
