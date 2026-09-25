from backend.app.models.entities import DraftPurchaseOrder,ExecutionAttempt
from backend.app.services.execution import DraftPOExecutionService

def test_unknown_lookup_requires_existing_po(db):
    po=DraftPurchaseOrder(po_reference='DPO-TEST',proposal_id=1,supplier_id='S1',supplier_name='S',product_code='P1',product_name='P',quantity=10,unit_cost=5,estimated_value=50,status='EXECUTION_UNKNOWN',execution_status='UNKNOWN',execution_idempotency_key='KEY-1',execution_attempts=1)
    db.add(po); db.commit()
    db.add(ExecutionAttempt(draft_po_id=po.id,po_reference=po.po_reference,attempt_no=1,idempotency_key='KEY-1',status='UNKNOWN',actor='system'))
    db.commit()
    view=DraftPOExecutionService(db).find_unknown('KEY-1')
    assert view['reconciliation_required'] is True
