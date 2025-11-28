# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine, init_db
from .models import models  # registra todos los modelos en Base

from .routers import (
    routes_analytics,
    routes_products,
    routes_order_items,
    routes_users,
    routes_roles,
    routes_product_comments,
    routes_orders,
    routes_comments,
    routes_auth,
    routes_cart,  
    routes_admin,
    routes_sales,
    routes_premium,
)

app = FastAPI(title="Ecom MKT Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "https://devops-tpi-final-hastesters.onrender.com"
        # después agregás la URL de Render del frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    init_db()

app.include_router(routes_roles.router)
app.include_router(routes_users.router)
app.include_router(routes_products.router)
app.include_router(routes_product_comments.router)
app.include_router(routes_orders.router)
app.include_router(routes_comments.router)
app.include_router(routes_auth.router)
app.include_router(routes_cart.router)
app.include_router(routes_admin.router)
app.include_router(routes_sales.router)
app.include_router(routes_order_items.router)
app.include_router(routes_analytics.router)
app.include_router(routes_premium.router)
