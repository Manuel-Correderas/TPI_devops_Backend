# conexion_postgres.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def conectar():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está definida")
    return psycopg2.connect(url)
