# tests/test_users_endpoint.py

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import Base, engine
from backend.app.models.models import User
from sqlalchemy import Boolean

client = TestClient(app)


def test_premium_es_boolean_en_modelo():
    col = User.__table__.c.premium
    assert isinstance(col.type, Boolean), f"premium NO es Boolean, es {col.type!r}"


def test_post_users_crea_usuario_201():
    Base.metadata.create_all(bind=engine)

    payload = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "tipo_doc": "DNI",
        "nro_doc": "99999999",
        "email": "juan_endpoint@example.com",
        "tel": "123456",
        "palabra_seg": "gato",
        "password": "Test123!",
        "acepta_terminos": True,
        "domicilio_envio": None,
        "domicilio_entrega": {
          "tipo": "ENTREGA",
          "calle_y_numero": "Calle 123",
          "ciudad": "",
          "provincia": "",
          "pais": "",
          "cp": ""
        },
        "banking": None,
        "wallets": None,
        "roles": ["COMPRADOR"],
        "premium": False  # 👈 OJO: boolean, no 0/1
    }

    r = client.post("/users", json=payload)
    assert r.status_code == 201, r.text

    data = r.json()
    assert "id" in data
    assert data["email"] == "juan_endpoint@example.com"
