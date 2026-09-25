from fastapi import FastAPI
from backend.app.core.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes import router
from backend.app.api.ingestion import router as ingestion_router
from backend.app.api.audit import router as audit_router

init_db()
app=FastAPI(title='MARG Procurement Agent',version='1.2.0',description='Reusable local-first, human-approved pharmaceutical procurement agent.')
app.include_router(router)
app.include_router(ingestion_router)
app.include_router(audit_router)

@app.get('/')
def root():
    return {'name':'MARG Procurement Agent','version':'1.2.0','docs':'/docs','execution_mode':settings.execution_mode}
