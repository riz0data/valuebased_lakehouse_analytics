# ISO/IEC 42001 Alignment

This document maps the technical controls already built in this project
against ISO/IEC 42001, the certifiable international standard for AI
management systems. It is a companion to `NIST_AI_RMF_alignment.md`,
not a replacement for it - the two frameworks are complementary rather
than competing: NIST AI RMF supplies a voluntary risk vocabulary, while
ISO 42001 supplies the certifiable management-system structure an
organization would build around that vocabulary.

**What this document is, and is not.** As with the NIST mapping, this
is a translation exercise, not a certification claim. ISO 42001
certification requires a Stage 1 and Stage 2 external audit, a
functioning management system sustained over time, and organizational
structures - a board, assigned role authorities, a management review
cycle - that no single repository can claim to have on its own. What
follows maps specific, already-built technical controls to the ISO
42001 structure they provide evidence toward, and names plainly what
a real certification effort would still require.

ISO 42001 has two parts: the main clauses (4 through 10), which
describe the management system itself - context, leadership, planning,
support, operation, evaluation, and improvement - and Annex A, a set of
38 AI-specific controls organized into nine control areas (A.2 through
A.10) covering AI policy, internal organization, resources, impact
assessment, the AI system lifecycle, data for AI systems, information
for interested parties, and use of AI systems.

---

## Main clauses (4 to 10): the management system itself

These clauses describe the system, not individual safeguards - they
ask whether a functioning, sustained management structure exists
around the AI controls.

**What this project provides evidence toward:**

- The `docs/decisions/ADRs.md` decision log functions as a working,
  dated record of planning and decision-making (clause 6, Planning) -
  each ADR documents a risk being reasoned about and a decision made,
  which is the same kind of evidence clause 6 asks an auditor to see.
- **ADR-009**'s evaluation harness and **ADR-008**'s observability
  logging are both a working instance of clause 9, Performance
  Evaluation - metrics are actually measured against a baseline
  (the golden dataset pass rate, the alerting thresholds) rather than
  just described as a plan.

**What's missing for a real implementation:**

- No leadership clause evidence (clause 5) - there's no documented
  executive sponsorship, AI policy statement, or management review
  cycle, since this is a single-contributor portfolio project rather
  than an organization with a leadership structure to document.
- No clause 4 context-of-the-organization documentation - who the
  interested parties are, what the organization's scope of certification
  would even be - since there's no organization here, only a project.
- No clause 10 continual-improvement cycle - improvements have happened
  session to session, but there's no formal review-and-improve process
  recorded as such.

---

## Annex A.2 to A.4: AI policy, internal organization, resources

These controls ask for a documented AI policy, assigned internal roles
with real authority, and resourcing for AI risk management.

**What this project provides evidence toward:**

- **ADR-006** (AI Agent Access Through the Semantic Layer, Not Raw SQL)
  functions as a de facto AI usage policy for this project - it states,
  in writing, the rule that governs how an agent is allowed to touch
  data.

**What's missing for a real implementation:**

- No internal organization control (A.3) - ISO 42001 wants documented
  role authorities, for example an AI system owner with actual
  authority to halt a system, not just a title. Nothing in this project
  assigns that authority to a named role.
- No resourcing statement (A.4) - there's no documented commitment of
  people, tooling budget, or time allocated to sustaining AI risk
  management, since that's an organizational commitment this project
  can't make on its own.

---

## Annex A.5: Impact assessment

This control area asks for a documented AI system impact assessment,
covering risks and impacts before deployment.

**What this project provides evidence toward:**

- The **Data Gap** documentation in `_metrics.yml` (for example, Medical
  Loss Ratio being explicitly flagged as unavailable) and **ADR-007's**
  documented row-filter limitation are both real, working instances of
  impact assessment - a risk was identified and written down rather
  than discovered after the fact.

**What's missing for a real implementation:**

- No formal impact assessment document distinct from these scattered
  ADR call-outs - ISO 42001 expects a structured assessment covering
  intended use, affected stakeholders, and severity, not individual
  notes captured decision by decision.

---

## Annex A.6: AI system life cycle

This control area maps to the classic development and operations
pipeline, expecting structure and traceability from initial concept
through to decommissioning.

**What this project provides evidence toward:**

- **`observability/evaluation/`** (ADR-009) and
  **`observability/guardrails/`** (ADR-010) are real, working lifecycle
  controls - evaluation before trusting agent output, guardrails at
  both the pre-call and post-call stage, both of which are exactly the
  kind of lifecycle checkpoint A.6 asks for.
- The dbt validator itself (`scripts/validate_dbt_structure.py`),
  re-run clean throughout this project's build, is a working example of
  a lifecycle gate - a check that must pass before the model layer is
  considered sound.

**What's missing for a real implementation:**

- No decommissioning procedure - as in the NIST mapping, nothing here
  addresses how a metric or an agent integration would be safely
  retired, which A.6 explicitly expects lifecycle coverage to include.
- No formal change management process for promoting a change through
  environments - the validator would catch a regression, but there's no
  documented review-and-approval step around a change before it ships.

---

## Annex A.7: Data for AI systems

This control area asks organizations to document what data is used by
each AI system: source, format, volume, and data categories, including
personal or sensitive data.

**What this project provides evidence toward:**

- **`dbt/models/semantic/_metrics.yml`** meta blocks (domain, unit,
  synonyms, data_maturity) directly document what data each metric
  draws on and its maturity, which is the same documentation A.7 asks
  for at the data-source level.
- **`dbt/models/gold/governance_policies.sql`**'s column masks on
  `dim_member.birth_date` and race code are a direct, working control
  over sensitive data categories, exactly the kind of personal or
  sensitive data handling A.7 calls out by name.

**What's missing for a real implementation:**

- No consolidated data inventory document - the information exists,
  spread across `_metrics.yml` and the governance policies file, but
  A.7 expects it drawn together into one reviewable record.

---

## Annex A.8 to A.10: Information for interested parties, use of AI systems

These controls ask whether interested parties are informed about the
AI system's use, and whether use of the system is itself governed.

**What this project provides evidence toward:**

- **`observability/README.md`**, **`observability/evaluation/README.md`**,
  and **`observability/guardrails/README.md`** collectively document,
  in plain language, what the agent can and can't do and how it's
  monitored - functioning as the kind of transparency artifact A.8
  expects, even though there's no external "interested party" reading
  them yet.

**What's missing for a real implementation:**

- No real interested-party communication process - the READMEs exist,
  but nothing routes them to an actual external stakeholder or
  end user as ISO 42001 would expect once the system is live for
  real users.

---

## Summary: NIST AI RMF versus ISO 42001, side by side

The NIST mapping and this one land in the same place for the same
reason: the technical controls in this project, observability,
evaluation, guardrails, and access control, are real and working, and
they give genuine evidence toward both frameworks' technical
expectations. What's missing in both cases is the same organizational
layer neither framework will let a codebase substitute for: assigned
role authority with real power to act, a leadership and policy
structure, a sustained review cycle, and a real external interested
party to be transparent with. ISO 42001 makes that gap slightly more
visible than NIST does, because ISO is built to be audited by a third
party against exactly that organizational structure, while NIST AI RMF
is voluntary guidance that never asked for the audit in the first
place.
