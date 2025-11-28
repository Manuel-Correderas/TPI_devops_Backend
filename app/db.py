# backend/app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os
from typing import Generator

# Carga variables desde .env (en local)
load_dotenv()

raw_db_url = os.getenv("DATABASE_URL")
if not raw_db_url:
    raise RuntimeError(
        "DATABASE_URL no está definida. Configurala en el archivo .env o en las variables de entorno."
    )

# Render suele dar "postgres://..." pero SQLAlchemy moderno quiere "postgresql+psycopg2://..."
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)

DATABASE_URL = raw_db_url

# Para SQLite local todavía soportamos el check_same_thread
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,  # ponelo True si querés ver las queries en consola
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
    pass


def get_db() -> Generator:
    """
    Dependency para FastAPI.
    Abre una sesión por request y la cierra al final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Registra los modelos y asegura que las tablas existan.
    No rompe nada si ya están creadas en Postgres.
    """
    from .models import models as m

    _ = (
        m.User,
        m.Address,
        m.BankingInfo,
        m.CryptoWallet,
        m.KYCDocument,
        m.Role,
        m.UserRole,
        m.Category,
        m.Product,
        m.ProductImage,
        m.ProductComment,
        m.Cart,
        m.CartItem,
        m.Order,
        m.OrderItem,
        m.Payment,
    )

    Base.metadata.create_all(bind=engine)
