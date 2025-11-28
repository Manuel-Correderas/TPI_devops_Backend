# debug_imports.py
import os
import sys

print("🚀 Iniciando debug de imports...")

# 1) Aseguramos que el root del proyecto esté en sys.path
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 2) Evitar que falle por falta de DATABASE_URL
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_debug.db")

print("📦 Probando importar deps...")
from backend.app.deps import get_current_user
print("✅ deps importado OK")

print("📦 Probando importar security...")
from backend.app.security import hash_password
print("✅ security importado OK")

print("🎉 Todo se importó sin circular imports ni errores de configuración.")
