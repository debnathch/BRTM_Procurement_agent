from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from backend.app.db.dependencies import get_db
from backend.app.services.audit_query import query_audit

router=APIRouter(prefix='/api/audit',tags=['audit'])
@router.get('/events')
def events(event_type:str|None=None,actor:str|None=None,outcome:str|None=None,db:Session=Depends(get_db)):
    types=[x.strip() for x in event_type.split(',') if x.strip()] if event_type else None
    return {'events':query_audit(db,types,actor,outcome)}
