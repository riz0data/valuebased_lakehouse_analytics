"""
governance_registry_check.py

A lightweight automation that reads docs/governance/registry/
governance_registry.xlsx - the single-point-of-reference spreadsheet
for this project's access rules, identities, and framework mappings -
and checks it against what is actually implemented in
dbt/models/gold/governance_policies.sql, flagging drift in either
direction: a rule the spreadsheet documents that the code no longer
implements, or a rule the code implements that the spreadsheet has not
been updated to reflect.

This exists because governance metadata drifts. A spreadsheet is
usually the artifact a compliance reviewer actually reads and trusts;
the SQL is the artifact that actually runs. Nothing enforces that they
stay in sync by construction, so this script is the enforcement point -
run manually today, but written to be dropped into a CI check or a
scheduled Databricks Job exactly as the rest of observability/ already
is (see ADR-017 in docs/decisions/ADRs.md).

This is a reference implementation: it parses governance_policies.sql
with regular expressions tuned to that file's actual structure, not a
general-purpose SQL parser. It is accurate against the file as it
exists today and is meant to be extended, not treated as a robust SQL
DDL parser for arbitrary input.
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_XLSX = REPO_ROOT / "docs" / "governance" / "registry" / "governance_registry.xlsx"
GOVERNANCE_SQL = REPO_ROOT / "dbt" / "models" / "gold" / "governance_policies.sql"


@dataclass
class DriftFinding:
    severity: str   # "documented_not_implemented" | "implemented_not_documented" | "ok"
    rule_id: Optional[str]
    table: str
    detail: str


def load_documented_rules() -> list[dict]:
    """Reads the 'Access Rules' sheet from the registry spreadsheet."""
    wb = openpyxl.load_workbook(REGISTRY_XLSX, data_only=True)
    ws = wb["Access Rules"]

    rules = []
    header_row = 4
    headers = [c.value for c in ws[header_row]]
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if row[0] is None:
            continue
        rules.append(dict(zip(headers, row)))
    return rules


def extract_implemented_tables_and_functions() -> set:
    """
    Parses governance_policies.sql for ALTER TABLE ... SET ROW FILTER
    and ALTER COLUMN ... SET MASK statements, returning a set of
    (table, function) pairs actually implemented in the SQL.

    Deliberately simple regex matching, not a full SQL parser - this is
    accurate against this file's actual, consistent formatting, and is
    meant to be extended if the file's structure changes materially.
    """
    text = GOVERNANCE_SQL.read_text()

    implemented = set()

    row_filter_pattern = re.compile(
        r"ALTER TABLE\s+([\w.]+)\s+SET ROW FILTER\s+([\w.]+)", re.IGNORECASE
    )
    for table, func in row_filter_pattern.findall(text):
        implemented.add((table, func))

    mask_pattern = re.compile(
        r"ALTER TABLE\s+([\w.]+)\s+ALTER COLUMN\s+\w+\s+SET MASK\s+([\w.]+)", re.IGNORECASE
    )
    for table, func in mask_pattern.findall(text):
        implemented.add((table, func))

    return implemented


def check_drift():
    findings = []

    documented_rules = load_documented_rules()
    implemented_pairs = extract_implemented_tables_and_functions()

    matched_implemented = set()

    for rule in documented_rules:
        control_type = (rule.get("Control Type") or "")
        table = rule.get("Table") or ""
        function = rule.get("Function") or ""

        if "Gap" in control_type or function.strip().lower().startswith("n/a"):
            # This row documents a known, intentional gap - not a claim
            # that the control exists, so there is nothing to check it
            # against. Recorded as informational, not a finding.
            findings.append(DriftFinding(
                severity="ok",
                rule_id=rule.get("Rule ID"),
                table=table,
                detail="Documented as a known gap ('%s'), not checked against code - as intended." % control_type,
            ))
            continue

        pair = (table, function)
        if pair in implemented_pairs:
            matched_implemented.add(pair)
            findings.append(DriftFinding(
                severity="ok",
                rule_id=rule.get("Rule ID"),
                table=table,
                detail="Documented rule '%s' on '%s' confirmed present in governance_policies.sql." % (function, table),
            ))
        else:
            findings.append(DriftFinding(
                severity="documented_not_implemented",
                rule_id=rule.get("Rule ID"),
                table=table,
                detail=(
                    "Registry documents '%s' on '%s', but this exact "
                    "table/function pair was not found in governance_policies.sql. "
                    "Either the code has drifted from the spreadsheet, or the "
                    "spreadsheet is stale." % (function, table)
                ),
            ))

    # Reverse direction: anything implemented in SQL that the registry
    # never mentions at all.
    for table, func in implemented_pairs:
        if (table, func) not in matched_implemented:
            findings.append(DriftFinding(
                severity="implemented_not_documented",
                rule_id=None,
                table=table,
                detail=(
                    "governance_policies.sql implements '%s' on '%s', but no row "
                    "in the registry's Access Rules sheet documents it - the spreadsheet "
                    "needs a new row, or this is an undocumented control." % (func, table)
                ),
            ))

    return findings


def run_check() -> int:
    """Returns 0 if no drift found, 1 otherwise - suitable for a CI
    exit code, same pattern as scripts/validate_dbt_structure.py."""
    findings = check_drift()

    ok = [f for f in findings if f.severity == "ok"]
    drift = [f for f in findings if f.severity != "ok"]

    print("Governance registry drift check: %s" % REGISTRY_XLSX.relative_to(REPO_ROOT))
    print("  %d rule(s) confirmed consistent between registry and code." % len(ok))
    print("  %d drift finding(s).\n" % len(drift))

    for f in ok:
        print("  OK  [%s] %s" % (f.rule_id, f.detail))

    if drift:
        print()
        for f in drift:
            label = "[%s]" % f.rule_id if f.rule_id else "[undocumented]"
            print("  DRIFT %s (%s): %s" % (label, f.severity, f.detail))

    print()
    if drift:
        print("FAILED: %d drift finding(s) - registry and code have diverged." % len(drift))
        return 1
    else:
        print("PASSED: registry and code are consistent.")
        return 0


if __name__ == "__main__":
    sys.exit(run_check())
