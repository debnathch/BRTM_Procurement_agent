"""Controlled execution of manager-approved draft purchase orders."""

import json
import secrets
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.adapters.executor import build_executor
from backend.app.core.config import settings
from backend.app.models.entities import DraftPurchaseOrder, ProcurementProposal, Supplier, ExecutionAttempt, AuditEvent
from backend.app.services.audit import audit

class DraftPOExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, po_id: int, actor: str = 'system') -> dict:
        po = self.db.get(DraftPurchaseOrder, po_id)
        if not po:
            raise ValueError('Draft purchase order not found.')
        if po.execution_status == 'SUCCEEDED' and po.execution_reference:
            audit(self.db, 'PO_EXECUTION_IDEMPOTENT_REPLAY', actor=actor,
                  entity_type='draft_purchase_order', entity_id=str(po.id),
                  details={'po_reference': po.po_reference, 'execution_reference': po.execution_reference})
            self.db.commit()
            return self._result(po, 'Idempotent replay: purchase order was already executed.')

        if po.status not in ('APPROVED_FOR_EXECUTION', 'EXECUTION_FAILED'):
            raise ValueError(f'Only approved draft purchase orders can be executed; current state is {po.status}.')
        if po.execution_status in ('IN_PROGRESS', 'UNKNOWN'):
            raise ValueError(f'Execution is {po.execution_status}; reconcile the existing attempt before retrying.')

        is_retry = po.execution_status == 'FAILED'
        supplier = self.db.get(Supplier, po.supplier_id)
        if not supplier or not supplier.is_active:
            raise ValueError('An active supplier is required for execution.')
        proposal = self.db.get(ProcurementProposal, po.proposal_id)
        if not proposal:
            raise ValueError('Source proposal no longer exists.')

        key = self._new_key(po) if is_retry else (po.execution_idempotency_key or self._new_key(po))
        if is_retry:
            audit(self.db, 'PO_EXECUTION_RETRY_DECISION', actor=actor,
                  entity_type='draft_purchase_order', entity_id=str(po.id),
                  details={'po_reference': po.po_reference, 'decision': 'RETRY',
                           'previous_execution_status': po.execution_status,
                           'attempt_no': (po.execution_attempts or 0) + 1,
                           'idempotency_key': key})
        po.execution_idempotency_key = key
        po.execution_status = 'IN_PROGRESS'
        po.execution_attempts = (po.execution_attempts or 0) + 1
        po.execution_started_at = datetime.utcnow()
        attempt_no = po.execution_attempts

        attempt = ExecutionAttempt(
            draft_po_id=po.id,
            po_reference=po.po_reference,
            attempt_no=attempt_no,
            idempotency_key=key,
            status='IN_PROGRESS',
            actor=actor,
            request_json=json.dumps(self._request_payload(po), sort_keys=True),
        )
        self.db.add(attempt)
        audit(self.db, 'PO_EXECUTION_STARTED', actor=actor, entity_type='draft_purchase_order',
              entity_id=str(po.id), details={'po_reference': po.po_reference, 'attempt_no': attempt_no, 'idempotency_key': key})
        self.db.commit()

        result = build_executor().create_purchase_order(
            supplier_id=po.supplier_id,
            company_code=settings.marg_company_code,
            items=[{'product_code': po.product_code, 'quantity': po.quantity, 'unit_cost': po.unit_cost}],
            remark=proposal.human_reason or f'Approved draft PO {po.po_reference}',
            idempotency_key=key,
        )

        now = datetime.utcnow()
        attempt.finished_at = now
        attempt.reference = result.reference or None
        attempt.response_message = result.message
        attempt.response_json = json.dumps({'reference': result.reference, 'message': result.message})

        if result.success:
            po.status = 'EXECUTED'
            po.execution_status = 'SUCCEEDED'
            po.execution_reference = result.reference
            po.executed_at = now
            proposal.status = 'EXECUTED'
            proposal.execution_reference = result.reference
            proposal.executed_at = now
            attempt.status = 'SUCCEEDED'
            event = 'PURCHASE_ORDER_EXECUTED'
        elif result.message.startswith('UNKNOWN:'):
            po.status = 'EXECUTION_UNKNOWN'
            po.execution_status = 'UNKNOWN'
            attempt.status = 'UNKNOWN'
            event = 'PURCHASE_ORDER_EXECUTION_UNKNOWN'
        else:
            po.status = 'EXECUTION_FAILED'
            po.execution_status = 'FAILED'
            attempt.status = 'FAILED'
            event = 'PURCHASE_ORDER_EXECUTION_FAILED'

        audit(self.db, event, actor=actor, entity_type='draft_purchase_order', entity_id=str(po.id),
              details={'po_reference': po.po_reference, 'attempt_no': attempt_no, 'idempotency_key': key,
                       'status': attempt.status, 'reference': result.reference, 'message': result.message})
        self.db.commit()
        return self._result(po, result.message)

    def find_unknown(self, lookup: str) -> dict:
        lookup = (lookup or '').strip()
        if not lookup:
            raise ValueError('Provide an idempotency key or MARG reference.')
        po = self.db.scalar(select(DraftPurchaseOrder).where(DraftPurchaseOrder.execution_idempotency_key == lookup))
        if not po:
            po = self.db.scalar(select(DraftPurchaseOrder).where(DraftPurchaseOrder.execution_reference == lookup))
        if not po:
            attempt = self.db.scalar(select(ExecutionAttempt).where(ExecutionAttempt.idempotency_key == lookup))
            if attempt:
                po = self.db.get(DraftPurchaseOrder, attempt.draft_po_id)
        if not po:
            raise ValueError('No draft PO found for the supplied idempotency key or MARG reference.')
        audit(self.db, 'PO_EXECUTION_RECONCILIATION_LOOKUP', actor='system',
              entity_type='draft_purchase_order', entity_id=str(po.id),
              details={'lookup': lookup, 'lookup_type': self._lookup_type(lookup, po),
                       'execution_status': po.execution_status,
                       'execution_reference': po.execution_reference})
        self.db.commit()
        return self._reconciliation_view(po)

    def reconcile_by_lookup(self, lookup: str, confirmed: bool, reference: str | None, actor: str, reason: str | None):
        view = self.find_unknown(lookup)
        return self.reconcile_unknown(view['po_id'], confirmed, reference, actor, reason)

    def _reconciliation_view(self, po):
        attempts = self.db.scalars(select(ExecutionAttempt).where(ExecutionAttempt.draft_po_id == po.id).order_by(ExecutionAttempt.attempt_no.desc())).all()
        audit_events = self.db.scalars(select(AuditEvent).where(
            AuditEvent.entity_type == 'draft_purchase_order',
            AuditEvent.entity_id == str(po.id)
        ).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())).all()
        history = []
        for event in audit_events:
            try:
                details = json.loads(event.details_json or '{}')
            except (TypeError, ValueError):
                details = {}
            history.append({
                'id': event.id, 'event_type': event.event_type, 'actor': event.actor,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'details': details,
            })
        return {
            'po_id': po.id, 'po_reference': po.po_reference, 'supplier_id': po.supplier_id,
            'supplier_name': po.supplier_name, 'product_code': po.product_code, 'product_name': po.product_name,
            'quantity': po.quantity, 'estimated_value': po.estimated_value, 'status': po.status,
            'execution_status': po.execution_status, 'execution_reference': po.execution_reference,
            'execution_idempotency_key': po.execution_idempotency_key, 'execution_attempts': po.execution_attempts,
            'reconciliation_required': po.execution_status == 'UNKNOWN',
            'audit_history': history,
            'attempts': [{'attempt_no': a.attempt_no, 'status': a.status, 'idempotency_key': a.idempotency_key,
                          'reference': a.reference, 'actor': a.actor, 'response_message': a.response_message,
                          'started_at': a.started_at.isoformat() if a.started_at else None,
                          'finished_at': a.finished_at.isoformat() if a.finished_at else None} for a in attempts]
        }

    def reconcile_unknown(self, po_id: int, confirmed: bool, reference: str | None, actor: str = 'human-ui', reason: str | None = None):
        po = self.db.get(DraftPurchaseOrder, po_id)
        if not po:
            raise ValueError('Draft purchase order not found.')
        if po.execution_status != 'UNKNOWN':
            raise ValueError(f'Only UNKNOWN executions can be reconciled; current state is {po.execution_status}.')
        attempt = self.db.scalar(select(ExecutionAttempt).where(ExecutionAttempt.draft_po_id == po.id).order_by(ExecutionAttempt.attempt_no.desc()))
        if not attempt:
            raise ValueError('No execution attempt exists for this PO.')
        audit(self.db, 'PO_EXECUTION_MANAGER_CONFIRMATION', actor=actor,
              entity_type='draft_purchase_order', entity_id=str(po.id),
              details={'po_reference': po.po_reference, 'outcome': 'CREATED' if confirmed else 'NOT_CREATED',
                       'reference': reference, 'reason': reason})
        if confirmed:
            if not reference:
                raise ValueError('MARG reference is required when confirming external execution.')
            po.status = 'EXECUTED'
            po.execution_status = 'SUCCEEDED'
            po.execution_reference = reference
            po.executed_at = datetime.utcnow()
            attempt.status = 'SUCCEEDED'
            attempt.reference = reference
            proposal = self.db.get(ProcurementProposal, po.proposal_id)
            if proposal:
                proposal.status = 'EXECUTED'
                proposal.execution_reference = reference
                proposal.executed_at = po.executed_at
            event = 'PO_EXECUTION_RECONCILED_SUCCEEDED'
        else:
            po.status = 'EXECUTION_FAILED'
            po.execution_status = 'FAILED'
            attempt.status = 'FAILED'
            event = 'PO_EXECUTION_RECONCILED_FAILED'
        audit(self.db, event, actor=actor, entity_type='draft_purchase_order', entity_id=str(po.id),
              details={'po_reference': po.po_reference, 'reference': reference, 'reason': reason})
        self.db.commit()
        return self._result(po, 'Execution reconciliation completed.')

    @staticmethod
    def _lookup_type(lookup, po):
        if lookup == po.execution_idempotency_key:
            return 'IDEMPOTENCY_KEY'
        if lookup == po.execution_reference:
            return 'MARG_REFERENCE'
        return 'EXECUTION_ATTEMPT_KEY'

    @staticmethod
    def _new_key(po):
        return f'{po.po_reference}-{secrets.token_hex(12)}'

    @staticmethod
    def _request_payload(po):
        return {'company_code': settings.marg_company_code, 'supplier_id': po.supplier_id,
                'items': [{'product_code': po.product_code, 'quantity': po.quantity, 'unit_cost': po.unit_cost}],
                'remark': po.po_reference}

    @staticmethod
    def _result(po, message):
        return {'status': po.status, 'execution_status': po.execution_status,
                'po_reference': po.po_reference, 'execution_reference': po.execution_reference,
                'idempotency_key': po.execution_idempotency_key, 'attempts': po.execution_attempts,
                'message': message}
