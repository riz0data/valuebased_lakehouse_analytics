# NIST AI RMF Alignment

This document maps the technical controls already built in this project
against the NIST AI Risk Management Framework (AI RMF 1.0), a voluntary,
principles-based framework built around four functions: Govern, Map,
Measure, and Manage.

**What this document is, and is not.** This is a translation exercise,
not a compliance claim. A real NIST AI RMF program means a documented
risk register, accountability structures, formal sign-off, and
continuous review at an organizational level - none of which a single
open-source portfolio repo can claim on its own. What follows maps
specific, already-built technical controls to the specific RMF
subcategories they provide evidence toward, using "maps to" language
throughout rather than "satisfies" or "complies with." It also names,
plainly, what a real implementation would still need that this project
does not and cannot provide alone.

ISO/IEC 42001, the certifiable AI management-system standard, and the
NIST AI RMF complement rather than compete with each other, so where
relevant this document notes ISO 42001 alignment too, without treating
it as a separate mapping exercise.

---

## GOVERN

GOVERN cultivates a risk-management culture and assigns roles and
accountability, and applies across every stage of the AI lifecycle,
not just a single point in time.

**What this project provides evidence toward:**

- **ADR-006** (AI Agent Access Through the Semantic Layer, Not Raw SQL)
  is a documented, dated governance decision with explicit rationale -
  the kind of accountability record GOVERN 1.1 and 1.2 ask for:
  inventorying how AI systems access data and defining risk tolerance
  before deployment.
- **ADR-007** (Unity Catalog row filters and column masks) and
  **ADR-010** (guardrails) are both dated decisions with explicit
  trade-off sections, showing risk tolerance being reasoned about
  and recorded, not just implemented silently.
- The `docs/decisions/ADRs.md` file as a whole functions as a real,
  versioned decision log - the closest thing this project has to the
  documented accountability trail GOVERN calls for.

**What's missing for a real implementation:**

- No actual assigned human roles or accountability structure - ADRs
  document decisions, not who is accountable for them ongoing.
- No documented organizational risk tolerance statement independent of
  individual ADRs - GOVERN wants a standing policy, not just a series
  of per-decision write-ups.
- No inventory of AI systems in use, since there is exactly one
  (simulated) agent integration in this project - a real GOVERN
  function assumes a portfolio of systems being tracked.

---

## MAP

MAP establishes context: what the AI system is for, who uses it, and
what could go wrong, before a go or no-go deployment decision.

**What this project provides evidence toward:**

- **`dbt/models/semantic/_metrics.yml`** meta blocks (domain, unit,
  synonyms, data_maturity added across all 26 metrics) directly serve
  MAP's context-establishment and system-categorization subcategories -
  every metric an agent can touch is scoped, labeled, and its data
  maturity flagged before an agent ever queries it.
- The **Data Gap** documentation (for example, Medical Loss Ratio,
  explicitly called out as unavailable) is a real, working example of
  MAP 2.2, identifying potential harms, in this case, the harm of an
  agent confidently answering with a metric that doesn't exist, headed
  off by declaring the gap in advance rather than discovering it live.
- **ADR-007's** explicit call-out that row filters don't cascade
  through joins to `fact_claim_payment` is a genuine, documented system
  limitation - exactly the kind of capability-and-limitation
  characterization MAP asks for, stated plainly rather than implied
  as covered.

**What's missing for a real implementation:**

- No stakeholder identification beyond an implicit "internal analyst or
  agent" user - a real MAP function documents the actual intended user
  population and any groups who could be adversely affected.
- No formal go/no-go decision record - the project was built
  iteratively rather than passing through an explicit MAP-gate before
  each stage was greenlit.

---

## MEASURE

MEASURE analyzes, benchmarks, and monitors AI risk using quantitative
or qualitative methods, on an ongoing basis, not just before launch.

**What this project provides evidence toward:**

- **`observability/mcp_audit_logger.py`** and the alerting rules in
  ADR-008 are a direct, working implementation of continuous
  monitoring: error rate, stuck-loop detection, and latency are all
  quantitatively tracked against fixed thresholds, matching MEASURE's
  call for ongoing benchmarking, not a one-time test.
- **`observability/evaluation/`** (ADR-009) is a direct, working
  implementation of MEASURE 2.1, documenting test results and
  evaluation results - the golden dataset pass rate and rubric scores
  are exactly the kind of evaluation record this subcategory asks for.
- The captured, real output files (`example_simulation_output.txt`,
  `example_eval_run_output.txt`, `example_guardrail_output.txt`) are
  themselves a small, honest version of the "database of reported
  errors and system changes" NIST's guidance describes - real
  evidence of what was tested and what happened, not just a claim.

**What's missing for a real implementation:**

- No live production traffic - everything measured here is either
  simulated or a one-time harness run, not the continuous, real-world
  measurement MEASURE ultimately expects once a system is deployed.
- No bias, fairness, or demographic-impact measurement - this project's
  metrics are financial and clinical-quality KPIs, not model predictions
  about people, so this gap is somewhat structural, but it's still a
  real category MEASURE covers that this project doesn't touch at all.

---

## MANAGE

MANAGE prioritizes and acts on identified risks, allocating resources
to treat them, and includes post-deployment monitoring, incident
response, and change management.

**What this project provides evidence toward:**

- **`observability/mcp_audit_logger.py`'s** alerting (`check_for_agent_anomalies`,
  writing trips to `gold.observability.agent_alerts`) is a direct,
  working implementation of MANAGE's post-deployment monitoring and
  incident-response subcategory - risks aren't just measured, they
  trigger a defined response path.
- **`observability/guardrails/guardrails.py`** (ADR-010) is MANAGE
  acting in real time rather than after the fact: BLOCK and REDACT
  decisions are risk treatment actually being executed, not just
  logged for later review.
- **ADR-007's** row filters and column masks are a standing, enforced
  risk-treatment control - access risk is managed continuously by the
  platform itself, not by periodic manual review.

**What's missing for a real implementation:**

- No real incident response process - alerts call a stand-in
  `send_alert()` function; nothing routes to an actual person, on-call
  rotation, or ticketing system.
- No change management process - there's no documented procedure for
  how a metric definition change gets reviewed, approved, and rolled
  out safely, only the fact that the golden dataset would catch a
  resulting regression if one were run.
- No decommissioning procedure - MANAGE 4.1 explicitly expects this;
  nothing in this project addresses how a metric or an agent
  integration would be safely retired.

---

## Summary: what's genuinely covered versus what's missing

This project has real, working evidence for parts of all four
functions, which is a stronger position than most portfolios reach, but
it is strongest in MEASURE and MANAGE's technical controls, and weakest
in the organizational and human-process parts of GOVERN and MAP that no
codebase can provide by itself: assigned accountability, a standing
risk tolerance policy, stakeholder identification, real incident
response, and change management process. That gap is expected and
should be stated plainly rather than glossed over - it's the honest
line between "a well-governed technical system" and "a certified AI
governance program," and this project is, deliberately, the former.
