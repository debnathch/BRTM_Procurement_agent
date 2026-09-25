from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.dependencies import get_db
from backend.app.schemas import DecisionRequest,DraftPOActionRequest,DraftPOReviewRequest,ProcurementRunRequest
from backend.app.agent.procurement_agent import ProcurementAgent
from backend.app.services.feedback import ProposalService
from backend.app.services.execution import DraftPOExecutionService

router=APIRouter(prefix='/api')

@router.get('/health')
def health():
    from backend.app.core.config import settings
    return {'status':'ok','execution_mode':settings.execution_mode}

@router.post('/procurement/run')
def run(req:ProcurementRunRequest,db:Session=Depends(get_db)):
    try:
        run_id,proposals=ProcurementAgent(db).run(req.product_codes)
        return {'run_id':run_id,'proposal_count':len(proposals)}
    except Exception as e: raise HTTPException(400,str(e))

@router.post('/proposals/{proposal_id}/decision')
def decision(proposal_id:int,req:DecisionRequest,db:Session=Depends(get_db)):
    try:return ProposalService(db).decide(proposal_id,req.action,req.approved_qty,req.supplier_id,req.reason,req.actor)
    except Exception as e:raise HTTPException(400,str(e))

@router.get('/draft-pos/{po_id}')
def draft_po(po_id:int,db:Session=Depends(get_db)):
    po=db.get(__import__('backend.app.models.entities',fromlist=['DraftPurchaseOrder']).DraftPurchaseOrder,po_id)
    if not po:raise HTTPException(404,'Draft PO not found')
    return {'po_id':po.id,'po_reference':po.po_reference,'status':po.status,'execution_status':po.execution_status,'supplier_id':po.supplier_id,'supplier_name':po.supplier_name,'product_code':po.product_code,'product_name':po.product_name,'quantity':po.quantity,'unit_cost':po.unit_cost,'estimated_value':po.estimated_value,'execution_reference':po.execution_reference,'attempts':po.execution_attempts}

@router.post('/draft-pos/{po_id}/review')
def review(po_id:int,req:DraftPOReviewRequest,db:Session=Depends(get_db)):
    try:return ProposalService(db).review_draft_po(po_id,req.quantity,req.supplier_id,req.reason,req.actor,False)
    except Exception as e:raise HTTPException(400,str(e))

@router.post('/draft-pos/{po_id}/approve-for-execution')
def approve_draft(po_id:int,req:DraftPOActionRequest,db:Session=Depends(get_db)):
    try:return ProposalService(db).review_draft_po(po_id,None,None,req.reason,req.actor,True)
    except Exception as e:raise HTTPException(400,str(e))

@router.post('/draft-pos/{po_id}/execution')
def execute(po_id:int,req:DraftPOActionRequest,db:Session=Depends(get_db)):
    try:return DraftPOExecutionService(db).execute(po_id,req.actor)
    except Exception as e:raise HTTPException(400,str(e))

@router.get('/execution/reconciliation/search')
def reconciliation_search(lookup:str,db:Session=Depends(get_db)):
    try:return DraftPOExecutionService(db).find_unknown(lookup)
    except Exception as e:raise HTTPException(404,str(e))

@router.post('/execution/reconciliation/resolve')
def reconciliation_resolve(lookup:str,confirmed:bool,reference:str|None=None,actor:str='human-ui',reason:str|None=None,db:Session=Depends(get_db)):
    try:return DraftPOExecutionService(db).reconcile_by_lookup(lookup,confirmed,reference,actor,reason)
    except Exception as e:raise HTTPException(400,str(e))
