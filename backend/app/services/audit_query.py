import csv,io,json
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.entities import AuditEvent

RECON_EVENTS={'PO_EXECUTION_RECONCILIATION_LOOKUP','PO_EXECUTION_MANAGER_CONFIRMATION','PO_EXECUTION_RECONCILED_SUCCEEDED','PO_EXECUTION_RECONCILED_FAILED','PO_EXECUTION_RETRY_DECISION'}

def query_audit(db,event_types=None,actor=None,outcome=None):
    rows=db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc(),AuditEvent.id.desc())).all()
    out=[]
    for e in rows:
        if event_types and e.event_type not in event_types:continue
        if actor and e.actor!=actor:continue
        try:d=json.loads(e.details_json or '{}')
        except: d={}
        if outcome and str(d.get('outcome','')).upper()!=outcome.upper():continue
        out.append({'id':e.id,'timestamp':e.created_at.isoformat() if e.created_at else '','event_type':e.event_type,'actor':e.actor,'outcome':d.get('outcome',''),'lookup':d.get('lookup',''),'marg_reference':d.get('reference') or d.get('execution_reference',''),'reason':d.get('reason',''),'attempt_no':d.get('attempt_no',''),'details':d})
    return out

def to_csv(rows):
    buf=io.StringIO(); fields=['timestamp','event_type','actor','outcome','lookup','marg_reference','reason','attempt_no','id']
    w=csv.DictWriter(buf,fieldnames=fields);w.writeheader()
    for r in rows:w.writerow({k:r.get(k,'') for k in fields})
    return buf.getvalue()
