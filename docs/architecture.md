# Architecture

MARG ERP is the transactional system of record.

MARG exports / future connector
→ ingestion adapter
→ validation + normalization
→ canonical SQLite/PostgreSQL-compatible model
→ procurement domain agent
→ demand + inventory + FEFO + supplier policy
→ deterministic guardrails
→ human approval
→ draft PO
→ execution adapter
→ reconciliation + audit + feedback

Execution defaults to dry-run. A live MARG connector must be implemented against the exact interface available in the customer's MARG deployment before enabling it.
