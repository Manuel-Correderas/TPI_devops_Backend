# backend/app/crud/user_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException

from ..models.models import (
    User,
    Role,
    UserRole,
    Address,
    BankingInfo,
    CryptoWallet,
)
from ..security import hash_password, verify_password
from ..schemas.user_schemas import UserCreate, AddressIn, CryptoWalletIn
from datetime import datetime


# ================================
# 📌 GETTERS
# ================================
def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


# ================================
# 📌 LOGIN
# ================================
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ================================
# 📌 ROLES
# ================================
def assign_roles(db: Session, user_id: str, role_codes: List[str]) -> None:
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()

    roles = db.query(Role).filter(Role.code.in_(role_codes)).all()
    for r in roles:
        db.add(UserRole(user_id=user_id, role_id=r.id))

    db.commit()


def seed_roles(db: Session) -> None:
    base = {
        "COMPRADOR": "Comprador",
        "VENDEDOR": "Vendedor",
        "ADMIN": "Administrador",
    }
    for code, nombre in base.items():
        if not db.query(Role).filter_by(code=code).first():
            db.add(Role(code=code, nombre=nombre))
    db.commit()


# ================================
# 📌 UPSERTS AUXILIARES
# ================================
def upsert_address(db: Session, user_id: str, addr_in: Optional[AddressIn]) -> None:
    if not addr_in:
        return

    row = db.query(Address).filter_by(user_id=user_id, tipo=addr_in.tipo).one_or_none()

    if row:
        for f in ("calle_y_numero", "ciudad", "provincia", "pais", "cp"):
            setattr(row, f, getattr(addr_in, f))
    else:
        db.add(Address(user_id=user_id, **addr_in.model_dump()))


def upsert_wallets(db: Session, user_id: str, wallets: Optional[List[CryptoWalletIn]]):
    if not wallets:
        return
    for w in wallets:
        row = db.query(CryptoWallet).filter_by(
            user_id=user_id, red=w.red
        ).one_or_none()
        if row:
            row.address = w.address
        else:
            db.add(CryptoWallet(user_id=user_id, red=w.red, address=w.address))


# ================================
# 📌 CREATE
# ================================
def create_user_full(db: Session, p: UserCreate) -> User:

    # Validaciones
    if db.query(User).filter_by(email=p.email).first():
        raise HTTPException(409, "Email ya registrado")
    if db.query(User).filter_by(nro_doc=p.nro_doc).first():
        raise HTTPException(409, "Documento ya registrado")
    if "COMPRADOR" in p.roles and not p.domicilio_entrega:
        raise HTTPException(422, "COMPRADOR requiere domicilio de ENTREGA")
    if "VENDEDOR" in p.roles and (not p.banking or not p.wallets):
        raise HTTPException(422, "VENDEDOR requiere CBU/Alias y al menos una Wallet")

    # Crear usuario
    u = User(
        nombre=p.nombre,
        apellido=p.apellido,
        tipo_doc=p.tipo_doc,
        nro_doc=p.nro_doc,
        email=p.email,
        tel=p.tel,
        palabra_seg=p.palabra_seg or "",
        password_hash=hash_password(p.password),
        acepta_terminos=p.acepta_terminos,

        # CAMPOS NUEVOS
        premium=bool(getattr(p, "premium", False)),
        estado="ACTIVO",
        dni_bloqueado=False,
        reset_code_hash=None,
        reset_code_expires_at=None,
    )

    db.add(u)
    db.flush()  # genera ID

    # Relaciones
    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    if p.banking:
        db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)

    assign_roles(db, u.id, p.roles)

    db.commit()
    db.refresh(u)
    return u


# ================================
# 📌 UPDATE COMPLETO
# ================================
def update_user_full(db: Session, user_id: str, p: UserCreate) -> User:

    u = get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")

    # actualizar core
    u.nombre = p.nombre
    u.apellido = p.apellido
    u.tipo_doc = p.tipo_doc
    u.nro_doc = p.nro_doc
    u.email = p.email
    u.tel = p.tel
    u.palabra_seg = p.palabra_seg or ""
    u.acepta_terminos = p.acepta_terminos

    # premium
    premium=bool(getattr(p, "premium", False)),

    if p.password:
        u.password_hash = hash_password(p.password)

    # relaciones
    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    if p.banking:
        b = db.query(BankingInfo).filter_by(user_id=u.id).one_or_none()
        if b:
            b.cbu_o_alias = p.banking.cbu_o_alias
        else:
            db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)

    assign_roles(db, u.id, p.roles)

    db.commit()
    db.refresh(u)
    return u


# ================================
# 📌 DELETE COMPLETO
# ================================
def delete_user_full(db: Session, user_id: str) -> bool:
    u = db.get(User, user_id)
    if not u:
        return False

    # borrado manual de relaciones
    for ur in list(u.roles or []):
        db.delete(ur)

    for d in list(u.addresses or []):
        db.delete(d)

    for w in list(u.wallets or []):
        db.delete(w)

    if u.banking:
        db.delete(u.banking)

    for k in list(u.kyc_docs or []):
        db.delete(k)

    db.delete(u)
    db.commit()
    return True
