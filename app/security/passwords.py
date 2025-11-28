# backend/app/security/passwords.py

"""
Wrapper para mantener compatibilidad:
todos los hash/verify usan el mismo esquema
definido en backend.app.security.__init__.
"""

from . import hash_password, verify_password  # reusa las funciones centrales

__all__ = ["hash_password", "verify_password"]
