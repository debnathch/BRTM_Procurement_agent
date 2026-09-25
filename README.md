# BRTM Procurement Agent

[![Python tests](https://github.com/debnathch/BRTM_Procurement_agent/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/debnathch/BRTM_Procurement_agent/actions/workflows/pytest.yml)

Local-first pharmaceutical procurement agent for MARG ERP.

## Architecture

MARG remains the system of record:

MARG Excel / future MARG API
→ common ingestion & validation
→ canonical local data model
→ procurement agent
→ demand + inventory + supplier + FEFO
→ deterministic guardrails
→ human approval
→ draft PO
→ controlled execution / reconciliation
→ audit + feedback

## Safety defaults

- EXECUTION_MODE=dry_run
- REQUIRE_HUMAN_APPROVAL=true
- No autonomous purchase execution by default.
- MARG execution requires a separately validated connector.
- Unknown external execution results must be reconciled before retry.
- Idempotency keys protect against duplicate execution.
- Procurement decisions retain an audit trail.

## Current v12 capabilities

- Native MARG report-aware procurement workflow
- Demand and inventory calculations
- FEFO / expiry-aware procurement controls
- Human approval and draft purchase orders
- Controlled MARG execution boundary
- Idempotent execution handling
- UNKNOWN execution reconciliation
- Reconciliation audit history
- Saved audit-filter views in the Streamlit UI
- CSV export of filtered reconciliation audit history

## Local setup

Recommended Python: 3.12.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

In another terminal:

    source .venv/bin/activate
    streamlit run frontend/streamlit_app.py

API docs: http://127.0.0.1:8000/docs

UI: http://127.0.0.1:8501

## Repository scope

The repository is being populated from the validated v12 implementation while excluding local runtime artifacts such as SQLite databases, Python bytecode, .env, and cache directories.

The canonical project source remains modular: adapters, API, domain agent, database models, services, tests, frontend, templates and documentation.
