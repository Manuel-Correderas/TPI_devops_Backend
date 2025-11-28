# tests/conftest.py
import os
import sys
import pytest
from fastapi.testclient import TestClient

# ============================
# RUTA RAÍZ DEL PROYECTO
# ============================
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Aseguramos que 'backend' sea importable:  from backend.app.main import app
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ============================
# DB DE TEST: SQLITE LOCAL
# ============================
# Antes de importar backend.app.db, seteamos DATABASE_URL
# para que NO explote por falta de .env
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from backend.app.db import Base, engine, SessionLocal  # usa esa DATABASE_URL
from backend.app.main import app
from backend.app.deps import get_db


# ============================
# FIXTURES DE BASE DE DATOS
# ============================

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Crea todas las tablas al inicio de la sesión de tests,
    y las borra al final.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """
    Abre una sesión de DB para cada test.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """
    TestClient de FastAPI que usa la sesión de prueba
    en vez del get_db real.
    """
    # override del dependency get_db para que use db_session
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
