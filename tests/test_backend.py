# tests/test_backend.py
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
import os

# ========================================
# ⚙️ Fuerza DB de test (SQLite)
# ========================================
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_backend.db")

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models.models import User
from backend.app.security import hash_password

client = TestClient(app)

# Credenciales “reales” SOLO para este archivo de test
EMAIL_TEST = os.getenv("EMAIL_TEST", "admin_test@mktlab.com")
PASS_TEST = os.getenv("PASS_TEST", "123456")


# ========================================
# Helper: crear usuario local para tests
# ========================================
def crear_usuario_real_para_tests():
    """
    Crea (o recrea) un usuario admin para las pruebas
    usando la base de datos de test (SQLite).
    """
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(email=EMAIL_TEST).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            nombre="Admin",
            apellido="Test",
            tipo_doc="DNI",
            nro_doc="99999998",
            email=EMAIL_TEST,
            tel="555",
            palabra_seg="perro",
            password_hash=hash_password(PASS_TEST),
            acepta_terminos=True,
            premium=0,
            dni_bloqueado=False,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


# ========================================
# UNIT TESTS
# ========================================

def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


def test_login_invalid_credentials():
    resp = client.post("/auth/login", json={
        "email": "no_existe@example.com",
        "password": "incorrecta"
    })
    assert resp.status_code == 401


def test_login_valid_returns_token():
    crear_usuario_real_para_tests()

    resp = client.post("/auth/login", json={
        "email": EMAIL_TEST,
        "password": PASS_TEST
    })

    assert resp.status_code == 200, f"Body: {resp.text}"

    data = resp.json()
    assert data.get("access_token")
    assert data.get("token_type", "").lower() in ("bearer", "jwt", "")


def test_list_products_returns_list():
    resp = client.get("/products", params={"limit": 5, "offset": 0})
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    # Si hay productos, verificar campos
    if data:
        p0 = data[0]
        assert "id" in p0
        assert "name" in p0
        assert "price" in p0
        assert "stock" in p0


# ========================================
# HELPERS DE INTEGRACIÓN
# ========================================

def login_and_get_token():
    crear_usuario_real_para_tests()
    resp = client.post("/auth/login", json={
        "email": EMAIL_TEST,
        "password": PASS_TEST
    })
    assert resp.status_code == 200
    return resp.json().get("access_token")


def get_first_product_id_with_stock():
    """
    Helper: devuelve el id del primer producto con stock > 0.
    Si no hay productos o todos tienen stock 0, hace skip del test
    en vez de romper todo el suite.
    """
    resp = client.get("/products", params={"limit": 50, "offset": 0})
    assert resp.status_code == 200
    productos = resp.json()

    # Si no hay productos en la base, no tiene sentido testear el carrito.
    if not productos:
        pytest.skip("No hay productos creados en la base para probar el carrito.")

    # Buscamos uno con stock > 0
    for p in productos:
        stock = p.get("stock", 0) or 0
        try:
            stock = int(stock)
        except Exception:
            stock = 0
        if stock > 0:
            return p["id"]

    # Si llegamos acá, hay productos pero todos con stock 0
    pytest.skip("No hay productos con stock > 0 para testear el carrito.")


# ========================================
# INTEGRATION TESTS
# ========================================

def test_cart_requires_auth():
    resp = client.get("/cart")
    assert resp.status_code in (401, 403)


def test_integration_login_and_get_cart():
    token = login_and_get_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/cart", headers=headers)
    assert resp.status_code in (200, 204)


def test_integration_add_item_to_cart_and_list():
    token = login_and_get_token()
    headers = {"Authorization": f"Bearer {token}"}

    product_id = get_first_product_id_with_stock()

    resp_add = client.post("/cart/items", json={
        "product_id": product_id,
        "qty": 1
    }, headers=headers)

    assert resp_add.status_code in (200, 201)

    resp_cart = client.get("/cart", headers=headers)
    assert resp_cart.status_code == 200

    cart_data = resp_cart.json()
    items = cart_data.get("items", [])

    assert any(str(i.get("product_id")) == str(product_id) for i in items)
