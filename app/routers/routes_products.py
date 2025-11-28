# backend/app/routers/routes_products.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, require_vendor   # 👈 AHORA DESDE deps
from ..schemas.product_schemas import ProductCreate, ProductUpdate, ProductOut
from ..crud.product_crud import (
    get_product_by_id,
    list_products,
    create_product,
    update_product,
    soft_delete_product,
)
from ..models.models import User

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductOut])
def list_products_endpoint(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Listado público de productos (no requiere login).
    """
    products = list_products(
        db,
        q=q,
        category_id=category_id,
        seller_id=seller_id,
        limit=limit,
        offset=offset,
    )
    return products


@router.get("/{product_id}", response_model=ProductOut)
def get_product_endpoint(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Detalle de un producto por ID.
    """
    p = get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    return p


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_vendor: User = Depends(require_vendor),  # 👈 obliga a rol VENDEDOR
):
    """
    Crea un producto nuevo asociado al vendedor logueado.
    """
    p = create_product(db, seller_id=current_vendor.id, payload=payload)
    return p


@router.put("/{product_id}", response_model=ProductOut)
def update_product_endpoint(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_vendor: User = Depends(require_vendor),
):
    """
    Actualiza un producto existente.
    Solo el vendedor dueño del producto puede editar.
    """
    p = get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    if p.seller_id != current_vendor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No sos dueño de este producto",
        )

    return update_product(db, p, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: str,
    db: Session = Depends(get_db),
    current_vendor: User = Depends(require_vendor),
):
    """
    Baja lógica (soft delete) de un producto.
    Solo el vendedor dueño del producto puede darlo de baja.
    """
    p = get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    if p.seller_id != current_vendor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No sos dueño de este producto",
        )

    soft_delete_product(db, p)
    return
