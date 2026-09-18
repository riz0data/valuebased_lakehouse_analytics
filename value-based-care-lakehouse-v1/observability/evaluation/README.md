# Evaluation

Three-layer evaluation for whether an AI agent resolves questions to the
*correct* governed metric - not to be confused with `../` one level up,
which covers agent *reliability* (errors, stuck loops, latency). See
ADR-009 in `docs/decisions/ADRs.md` for the full design reasoning.

**No agent is actually deployed against this project.** This harness
runs today against a simple simulated stand-in
(`simulated_agent_resolve()`), so the evaluation logic itself is real
and runnable, ready to be pointed at a real agent's output the moment
one exists.

## Files

- `golden_dataset.json` - 28 test cases, generated directly from the
  real `meta.synonyms` entries in `dbt/models/semantic/_metrics.yml`:
  26 "should resolve correctly" cases (one per metric with synonyms),
  plus two deliberately adversarial cases - a legitimate "no match"
  (Medical Loss Ratio, a documented Data Gap) and a loose phrasing that
  doesn't literally contain a defined synonym.
- `evaluate_agent.py` - the three-layer harness. Run it directly:
  `python3 evaluate_agent.py`.
- `example_eval_run_output.txt` - real, captured output from running
  the harness: 27 of 28 cases pass; the one genuine failure is the
  adversarial loose-phrasing case, included on purpose to show an
  honest limitation rather than an all-green result.

## The three layers

1. **Deterministic checks** - near-zero cost, no model involved. Does
   the agent's claimed metric actually exist in `_metrics.yml`? Catches
   a hallucinated metric name before anything more expensive runs.
2. **Golden dataset exact match** - did the agent resolve to exactly
   the expected metric? Pass or fail, run against every case in
   `golden_dataset.json`.
3. **Rubric-based scoring** - for misses, how close was it? Same-domain
   misses score partial credit; completely unrelated misses, or a
   confident answer where "no match" was correct, score zero. This
   reference version is a deterministic function with the same
   inputs/outputs a real LLM-as-judge call would have, so it runs with
   no API key. Swapping in a real frontier-model (or small fine-tuned
   judge model) call is a localized change to one function, not a
   redesign - see ADR-009.

## Why three layers instead of just the golden dataset

A single fixed test set only catches exact-match failures, and treats
"completely wrong domain" the same as "picked a very similar but wrong
metric" - both just "fail." Layering in fast deterministic checks below
it, and rubric scoring above it, matches how the industry actually
evaluates agents: cheap checks run on everything, exact-match regression
tests run on known cases, and judge-based scoring adds nuance a binary
pass/fail throws away - typically sampled against live traffic rather
than only run offline before a release, once an agent is actually
deployed.

## What this doesn't cover

This evaluates whether the agent picked the *right metric* for a
question. It does not evaluate whether the number `query_metrics`
returns for that metric is itself correct - that correctness is already
guaranteed by construction, since the Semantic Layer computes the
number from a reviewed definition, not the agent (see ADR-006).
