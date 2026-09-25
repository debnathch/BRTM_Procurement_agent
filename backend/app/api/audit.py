from fastapi import APIRouter,Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.db.dependencies import get_db
from backend.app.services.audit_query import query_audit,to_csv

router=APIRouter(prefix='/api/audit',tags=['audit'])

@router.get('/events')
def events(event_type:str|None=None,actor:str|None=None,outcome:str|None=None,db:Session=Depends(get_db)):
    types=[x.strip() for x in event_type.split(',') if x.strip()] if event_type else None
    rows=query_audit(db,types,actor,outcome)
    return {'count':len(rows),'events':rows}

@router.get('/events.csv')
def events_csv(event_type:str|None=None,actor:str|None=None,outcome:str|None=None,db:Session=Depends(get_db)):
    types=[x.strip() for x in event_type.split(',') if x.strip()] if event_type else None
    content=to_csv(query_audit(db,types,actor,outcome))
    return StreamingResponse(iter([content]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=audit_history.csv'})
