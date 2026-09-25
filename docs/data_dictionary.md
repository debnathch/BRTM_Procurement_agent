# MARG Procurement Data Dictionary

The importer is intentionally report-aware. MARG Excel exports are not treated as one universal schema.

## Supported source profiles

- Sales report
- Purchase summary
- Stock / batch report
- Future pending purchase order export
- Future item master and supplier master

## Canonical identity

When a source report does not provide a stable MARG item code, the importer creates a deterministic technical identity:

MARGDESC-<SHA1(normalized item description)>

This is an integration key, not an invented business master code.

## Missing data

The system must not invent supplier, MOQ, pack size, lead time, customer demand or open-PO information. Missing required data should produce DATA INSUFFICIENT or a clearly labelled configurable assumption.

## Sales semantics

A MARG sales summary is a period summary, not a fabricated daily transaction stream. If the report covers N days, quantity can be normalized to an approximate daily rate using quantity / N, with free quantity and returns handled when present.

## Stock semantics

Stock is batch-level where the report supplies batch and expiry information. Unknown expiry values must remain unknown rather than being silently converted into a safe expiry date.
