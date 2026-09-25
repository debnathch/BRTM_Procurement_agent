from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.app.core.config import settings

class Base(DeclarativeBase): pass

if settings.database_url.startswith('sqlite:///'):
    Path('./data').mkdir(exist_ok=True)
engine=create_engine(settings.database_url,connect_args={'check_same_thread':False} if settings.database_url.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)

def init_db():
    from backend.app.models import entities
    Base.metadata.create_all(bind=engine)
