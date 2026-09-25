from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.entities import ProcurementProposal, FeedbackEvent, Product, Supplier, DraftPurchaseOrder
from backend.app.services.guardrails import ProcurementGuardrails
from backend.app.services.audit import audit
from backend.app.core.config import settings

class ProposalService:
    def __init__(self, db: Session):
        self.db = db
        self.guardrails = ProcurementGuardrails()

    def decide(self, proposal_id, action, approved_qty, supplier_id, reason, actor='human-ui'):
        proposal = self.db.get(ProcurementProposal, proposal_id)
        if not proposal: raise ValueError('Proposal not found.')
        product = self.db.get(Product, proposal.product_code)
        if not product: raise ValueError('Product for proposal no longer exists.')

        if action == 'reject':
            if proposal.status not in ('PENDING','HOLD'): raise ValueError(f'Cannot reject proposal in state {proposal.status}.')
            proposal.status='REJECTED'; proposal.human_reason=reason or 'Rejected by human reviewer.'
            self.db.add(FeedbackEvent(proposal_id=proposal.id, action='REJECT', original_qty=proposal.recommended_qty, final_qty=None, reason=proposal.human_reason))
            audit(self.db,'PROPOSAL_REJECTED',actor=actor,entity_type='proposal',entity_id=str(proposal.id),details={'reason':proposal.human_reason})
            self.db.commit(); return {'status':proposal.status,'reference':''}

        if action == 'hold':
            if proposal.status not in ('PENDING','APPROVED'): raise ValueError(f'Cannot hold proposal in state {proposal.status}.')
            proposal.status='HOLD'; proposal.human_reason=reason or 'Placed on hold by human reviewer.'
            self.db.add(FeedbackEvent(proposal_id=proposal.id, action='HOLD', original_qty=proposal.recommended_qty, final_qty=proposal.approved_qty, reason=proposal.human_reason))
            audit(self.db,'PROPOSAL_HELD',actor=actor,entity_type='proposal',entity_id=str(proposal.id),details={'reason':proposal.human_reason})
            self.db.commit(); return {'status':proposal.status,'reference':''}

        if action == 'approve':
            if proposal.status not in ('PENDING','HOLD'): raise ValueError(f'Cannot approve proposal in state {proposal.status}.')
            qty=float(approved_qty if approved_qty is not None else proposal.recommended_qty); sid=supplier_id or proposal.supplier_id
            supplier=self.db.get(Supplier,sid) if sid else None
            if supplier is None: raise ValueError('An active supplier is required for approval.')
            if not settings.allow_supplier_change and proposal.supplier_id and sid != proposal.supplier_id: raise ValueError('Changing supplier is disabled by policy.')
            guard=self.guardrails.validate_approval(proposal,product,supplier,qty)
            if not guard.allowed: raise ValueError('Guardrail blocked approval: '+' | '.join(guard.reasons))
            proposal.approved_qty=qty; proposal.supplier_id=supplier.supplier_id; proposal.supplier_name=supplier.supplier_name
            proposal.human_reason=reason or 'Approved by human reviewer.'; proposal.approved_at=datetime.utcnow(); proposal.status='APPROVED'
            self.db.add(FeedbackEvent(proposal_id=proposal.id,action='APPROVE' if qty==proposal.recommended_qty else 'MODIFY_APPROVE',original_qty=proposal.recommended_qty,final_qty=qty,reason=proposal.human_reason))
            audit(self.db,'PROPOSAL_APPROVED',actor=actor,entity_type='proposal',entity_id=str(proposal.id),details={'qty':qty,'supplier_id':supplier.supplier_id,'reason':proposal.human_reason})
            self.db.commit(); return {'status':proposal.status,'reference':'','message':'Approved only. No purchase order was created or executed.'}

        if action == 'create_draft_po':
            if proposal.status != 'APPROVED': raise ValueError('Proposal must be APPROVED before creating a draft purchase order.')
            existing=self.db.scalar(select(DraftPurchaseOrder).where(DraftPurchaseOrder.proposal_id==proposal.id,DraftPurchaseOrder.status=='DRAFT'))
            if existing: return {'status':proposal.status,'reference':existing.po_reference,'message':'Draft PO already exists.'}
            qty=float(proposal.approved_qty if proposal.approved_qty is not None else proposal.recommended_qty); sid=supplier_id or proposal.supplier_id
            supplier=self.db.get(Supplier,sid) if sid else None
            if supplier is None: raise ValueError('An active supplier is required to create a draft PO.')
            guard=self.guardrails.validate_approval(proposal,product,supplier,qty)
            if not guard.allowed: raise ValueError('Guardrail blocked draft PO: '+' | '.join(guard.reasons))
            import uuid
            ref='DPO-'+uuid.uuid4().hex[:10].upper()
            po=DraftPurchaseOrder(po_reference=ref,proposal_id=proposal.id,supplier_id=supplier.supplier_id,supplier_name=supplier.supplier_name,product_code=proposal.product_code,product_name=proposal.product_name,quantity=qty,unit_cost=proposal.unit_cost,estimated_value=qty*proposal.unit_cost,status='DRAFT',created_by=actor)
            self.db.add(po); proposal.execution_reference=ref; proposal.human_reason=reason or proposal.human_reason or 'Draft PO created.'
            self.db.add(FeedbackEvent(proposal_id=proposal.id,action='CREATE_DRAFT_PO',original_qty=proposal.recommended_qty,final_qty=qty,reason=proposal.human_reason))
            audit(self.db,'DRAFT_PO_CREATED',actor=actor,entity_type='proposal',entity_id=str(proposal.id),details={'draft_po_reference':ref,'qty':qty,'supplier_id':supplier.supplier_id,'value':po.estimated_value})
            self.db.commit(); return {'status':proposal.status,'reference':ref,'message':'Draft purchase order created. It has not been sent to MARG or executed.'}

    def review_draft_po(self, po_id, quantity, supplier_id, reason, actor, approve_for_execution=False):
        po=self.db.get(DraftPurchaseOrder,po_id)
        if not po: raise ValueError('Draft purchase order not found.')
        if po.status!='DRAFT': raise ValueError(f'Only DRAFT purchase orders can be reviewed; current state is {po.status}.')
        proposal=self.db.get(ProcurementProposal,po.proposal_id); product=self.db.get(Product,po.product_code)
        if not proposal or not product: raise ValueError('Draft PO source proposal/product no longer exists.')
        qty=float(quantity if quantity is not None else po.quantity); sid=supplier_id or po.supplier_id; supplier=self.db.get(Supplier,sid) if sid else None
        if supplier is None or not supplier.is_active: raise ValueError('An active supplier is required.')
        guard=self.guardrails.validate_approval(proposal,product,supplier,qty)
        if not guard.allowed: raise ValueError('Guardrail blocked draft PO review: '+' | '.join(guard.reasons))
        changed=qty!=po.quantity or sid!=po.supplier_id
        po.quantity=qty; po.supplier_id=supplier.supplier_id; po.supplier_name=supplier.supplier_name; po.estimated_value=qty*po.unit_cost
        proposal.approved_qty=qty; proposal.supplier_id=supplier.supplier_id; proposal.supplier_name=supplier.supplier_name; proposal.human_reason=reason or proposal.human_reason
        event='DRAFT_PO_REVIEWED'
        if approve_for_execution: po.status='APPROVED_FOR_EXECUTION'; proposal.execution_reference=po.po_reference; event='DRAFT_PO_APPROVED_FOR_EXECUTION'
        self.db.add(FeedbackEvent(proposal_id=proposal.id,action='REVIEW_DRAFT_PO' if not approve_for_execution else 'APPROVE_DRAFT_PO',original_qty=proposal.recommended_qty,final_qty=qty,reason=reason or ('Draft PO approved for execution.' if approve_for_execution else 'Draft PO reviewed.')))
        audit(self.db,event,actor=actor,entity_type='draft_purchase_order',entity_id=str(po.id),details={'po_reference':po.po_reference,'changed':changed,'new':{'quantity':qty,'supplier_id':supplier.supplier_id,'supplier_name':supplier.supplier_name,'estimated_value':po.estimated_value},'reason':reason})
        self.db.commit()
        return {'status':po.status,'po_reference':po.po_reference,'quantity':po.quantity,'supplier_id':po.supplier_id,'supplier_name':po.supplier_name,'estimated_value':po.estimated_value,'message':'Draft PO approved for execution. No external purchase was executed.' if approve_for_execution else 'Draft PO updated.'}
