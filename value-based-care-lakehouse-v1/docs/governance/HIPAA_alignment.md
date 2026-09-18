# HIPAA Technical Safeguards Alignment

This document maps controls already built and documented elsewhere in
this repo to HIPAA's Security Rule technical safeguards. It adds no new
mechanism - it re-states existing controls (ADR-007's row filters and
column masks, ADR-008's audit logger) in the vocabulary a healthcare
compliance reviewer would expect, following the same "maps to, does not
claim to satisfy" framing used in `NIST_AI_RMF_alignment.md` and
`ISO_42001_alignment.md`.

## What HIPAA actually is

HIPAA is not one rule but three: the Privacy Rule governs PHI use,
disclosure, and patient rights; the Security Rule mandates
administrative, physical, and technical safeguards for electronic PHI;
and the Breach Notification Rule sets notification obligations and
timelines. An architect's responsibility sits almost entirely inside
the Security Rule's technical safeguards, which define the
technologies required to secure ePHI against unauthorized access,
disclosure, and alteration, including access controls, encryption,
authentication, and secure transmission.

## Mapping this project's controls to technical safeguards

**Access control / minimum necessary.** HIPAA's minimum necessary
standard - exposing only the least data needed for a given purpose - is
implemented by `dbt/models/gold/governance_policies.sql`'s row filters
and column masks (ADR-007). Every identity, human or agent, only ever
sees the rows and columns its Unity Catalog grant permits; no query in
this project touches raw, ungoverned tables (ADR-006, the
semantic-layer-only rule). This is the access-control safeguard HIPAA's
technical safeguards require, already implemented as part of this
project's core governance design, now named explicitly in HIPAA's own
terms.

**Audit controls.** Audit controls are essential for demonstrating
HIPAA compliance, and organizations must implement mechanisms to
ensure ePHI is not altered or destroyed improperly. `mcp_audit_logger.py`
(ADR-008) logs every agent tool call - caller identity, arguments,
resolved metric, outcome - to a Delta table on a continuous cadence.
Functionally, this is the audit-control safeguard HIPAA requires,
though it was originally built for AI-agent observability rather than
compliance specifically; the mechanism transfers directly.

**Authentication.** ADR-013's identity layer - a distinct, scoped
service-principal identity for the agent, using short-lived OAuth
credentials rather than a static personal access token - is the
authentication safeguard for machine access, distinguishing agent
traffic from human traffic in a way HIPAA's technical safeguards
require but do not by themselves prescribe a mechanism for.

## Known gaps, stated honestly

HIPAA also requires administrative and physical safeguards -
workforce training, facility access controls, documented risk
assessments - and requires retaining compliance documentation and
audit logs for six years. None of this can be meaningfully demonstrated
by a synthetic-data portfolio project: there is no real workforce, no
real facility, and no real retained production history to point to.
This document maps only the technical-safeguard controls this repo
actually implements in code. It does not claim HIPAA compliance as a
whole, and should not be read as a substitute for a real risk
assessment or a signed Business Associate Agreement, both of which are
organizational and legal artifacts outside what a codebase alone can
provide.
