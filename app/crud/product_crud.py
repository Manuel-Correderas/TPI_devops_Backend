# backend/app/crud/product_crud.py
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.models import Product, ProductImage
from ..schemas.product_schemas import ProductCreate, ProductUpdate


# ============================
# Obtener 1 producto
# ============================
def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
    return (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )


# ============================
# Listar productos
# ============================
def list_products(
    db: Session,
    q: str | None,
    category_id: str | None,
    seller_id: str | None,
    limit: int = 20,
    offset: int = 0,
) -> List[Product]:

    query = db.query(Product).filter(Product.is_active == True)

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if seller_id:
        query = query.filter(Product.seller_id == seller_id)

    return (
        query.order_by(Product.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


# ============================
# Crear producto
# ============================
def create_product(db: Session, seller_id: str, payload: ProductCreate) -> Product:

    p = Product(
        seller_id=seller_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        condition=payload.condition,
        category_id=payload.category_id,
        subcategory=payload.subcategory,
        image_url=payload.image_url,
        is_active=payload.is_active,

        # NUEVOS CAMPOS
        rating=payload.rating,
        sold_count=payload.sold_count,
        features=payload.features,
        pay_method=payload.pay_method,
        network=payload.network,
        alias=payload.alias,
        wallet=payload.wallet,
    )

    db.add(p)
    db.flush()  # genera ID

    # Guardar imágenes si vienen en payload
    if payload.images:
        for i, url in enumerate(payload.images):
            db.add(ProductImage(product_id=p.id, url=url, sort_order=i))

    db.commit()
    db.refresh(p)
    return p


# ============================
# Actualizar producto
# ============================
def update_product(db: Session, p: Product, payload: ProductUpdate) -> Product:

    for k, v in payload.model_dump(exclude_unset=True).items():
        if k != "images":
            setattr(p, k, v)

    # Actualizar imágenes
    if payload.images is not None:
        # Borrar imágenes previas
        for im in list(p.images or []):
            db.delete(im)

        # Crear nuevas
        for i, url in enumerate(payload.images):
            db.add(ProductImage(product_id=p.id, url=url, sort_order=i))

    db.commit()
    db.refresh(p)
    return p


# ============================
# Baja lógica
# ============================
def soft_delete_product(db: Session, p: Product) -> None:
    p.is_active = False
    db.commit()
