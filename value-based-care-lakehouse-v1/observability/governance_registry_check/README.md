# Governance Registry & Drift Check

This is the single point of reference for this project's governance
metadata, and the automation that keeps it honest. See ADR-017 in
`docs/decisions/ADRs.md` for full reasoning.

## The registry spreadsheet

`docs/governance/registry/governance_registry.xlsx` consolidates what
was previously only prose spread across three separate alignment docs
into structured, checkable rows:

- **Access Rules** - every row filter and column mask this project
  defines, pulled directly from `dbt/models/gold/governance_policies.sql`
  (ADR-007), with the table, column, function, and framework tags each
  rule maps to.
- **Identities** - every human role and agent identity referenced by
  those access rules (ADR-007, ADR-013).
- **HIPAA Mapping**, **ISO 42001 Mapping**, **NIST AI RMF Mapping** -
  the same content as the three narrative alignment docs in
  `docs/governance/`, restructured as one row per control with an
  explicit status (Covered / Partially covered / Gap).
- **Gaps Register** - every honestly-stated gap across all three
  frameworks, consolidated in one sheet for a quick scan.

This spreadsheet does not replace the narrative docs - it consolidates
their structured facts into a format that can actually be checked
against code, which prose cannot be.

## The drift check

`governance_registry_check.py` reads the Access Rules sheet and parses
`governance_policies.sql` for its actual `SET ROW FILTER` and `SET
MASK` statements, then reports any mismatch in either direction: a
rule the spreadsheet claims exists that the SQL does not implement, or
a rule the SQL implements that the spreadsheet never documents. Rows
that document a known, intentional gap (rather than a claimed control)
are treated as informational and are not checked against code, since
there is nothing in the code for them to match.

This was verified against a real, deliberately introduced mismatch -
renaming a masking function in the SQL without updating the
spreadsheet - and correctly caught it as two drift findings in both
directions, then correctly reported zero drift once reverted.

## Run it

    python3 observability/governance_registry_check/governance_registry_check.py

Exits 0 with no drift, 1 if any drift is found - the same convention
`scripts/validate_dbt_structure.py` already uses, so this can be
dropped into the same CI step or a scheduled Databricks Job. Real
output from a clean run is saved in `example_check_output.txt`.

## Limits, stated honestly

The SQL parser is simple, tuned regular-expression matching against
this file's current, consistent formatting - not a general-purpose SQL
DDL parser. It is accurate against `governance_policies.sql` as it
exists today and would need extending if that file's structure changed
materially.

## Files

- `governance_registry_check.py` - the drift-checking automation.
- `example_check_output.txt` - real output from a clean run.
- `../../docs/governance/registry/governance_registry.xlsx` - the
  registry spreadsheet itself.
