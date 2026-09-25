import os
os.environ['DATABASE_URL']='sqlite:///:memory:'
from backend.app.db.database import Base,engine
import pytest
@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    from backend.app.db.database import SessionLocal
    s=SessionLocal()
    try:yield s
    finally:s.close()
