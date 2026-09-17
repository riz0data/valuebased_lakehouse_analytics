# Transactional Link Models

**Status: all 6 Transactional Links implemented - Payment Integrity, Risk Adjustment, Clinical Quality, and Pharmacy.**

Implemented: `tlnk_claim_payment_txn`, `tlnk_claim_adjustment_txn`,
`tlnk_cob_recovery_txn` - built using real `automate_dv.t_link()` macro
calls. All three are sourced from clearly-labeled SYNTHETIC fixtures (see
`ingestion/payment_integrity/README.md`) since no open dataset carries
claim-level payment/adjustment/COB transaction detail.

Risk Adjustment: `tlnk_member_risk_score_txn` - member RAF scores by
model year. SYNTHETIC RAF values (CMS does not publish member-level risk
scores) - see `ingestion/risk_adjustment/README.md`.

Clinical Quality: `tlnk_member_measure_eval_txn` - member quality
measure evaluation events. SYNTHETIC eval results (met/not_met) - see
`ingestion/clinical_quality/README.md`.

Pharmacy: `tlnk_pharmacy_fill_txn` - prescription fill events
(member + drug + pharmacy + fill_date + days_supply). SYNTHETIC - see
`ingestion/pharmacy/README.md`.

All 6 Transactional Links across every domain are now implemented.

## Transactional Link vs. Link

Transactional Links (`t_link()`) differ from ordinary Links (`link()`):
they represent immutable, append-only business events tied to a specific
point in time (a payment, an adjustment, a recovery), rather than a
durable many-to-many relationship between two business entities. Each
carries an `EFFECTIVE_FROM` date reflecting when the event itself
happened, separate from `LOAD_DATETIME` (when it arrived in the
warehouse) - see the automate_dv docs on Transactional Links for the
full rationale.
