from fastapi import FastAPI
from backend.app.core.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes import router

init_db()
app = FastAPI(
    title='MARG Procurement Agent',
    version='1.1.0',
    description='Reusable local-first, human-approved pharmaceutical procurement agent.',
)
app.include_router(router)

@app.get('/')
def root():
    return {'name': 'MARG Procurement Agent', 'version': '1.1.0', 'docs': '/docs', 'execution_mode': settings.execution_mode}
