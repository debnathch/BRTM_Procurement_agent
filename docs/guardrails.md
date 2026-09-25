# Procurement Guardrails

Hard gates include:

- human approval before external execution;
- positive quantity;
- pack-size compliance;
- proposal quantity/value caps;
- active supplier;
- reorder eligibility;
- expiry-risk blocking at configured threshold;
- idempotency for execution;
- UNKNOWN execution must be reconciled before retry.

Guardrails are deterministic and auditable. AI/model output cannot bypass them.
