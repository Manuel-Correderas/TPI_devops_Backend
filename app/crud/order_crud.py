# backend/app/crud/order_crud.py
from sqlalchemy.orm import Session

from ..models.models import Cart, Order, OrderItem, Payment


def checkout(db: Session, user_id: str, user_name: str | None = None) -> Order:
    """
    Crea una orden a partir del carrito del usuario:
    - Toma todos los ítems del carrito
    - Calcula el total
    - Crea Order + OrderItems
    - (Opcional) crea un Payment en estado PENDIENTE
    - Vacía el carrito
    """
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .first()
    )

    if not cart or not cart.items:
        raise ValueError("Carrito vacío")

    total = sum(ci.qty * ci.price for ci in cart.items)

    # ⚠️ El modelo Order tiene total_amount, no total
    order = Order(
        user_id=user_id,
        user_name=user_name,
        status="PENDIENTE",   # o "CREADA" si preferís
        total_amount=total,
    )
    db.add(order)
    db.flush()  # genera order.id

    # Crear OrderItems a partir del snapshot del carrito
    for ci in cart.items:
        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            product_name=ci.name,
            category=None,         # si después querés, podés traer la categoría real
            subcategory=None,
            seller=ci.seller,
            seller_id=None,        # idem, si querés, lo podés poblar
            company=None,
            quantity=ci.qty,
            unit_price=ci.price,
        )
        db.add(oi)

    # Crear un Payment “placeholder” en PENDIENTE
    payment = Payment(
        order_id=order.id,
        provider="MP",       # MP / TARJETA / TRANSFER
        status="PENDIENTE",
        amount=total,
        tx_ref=None,
    )
    db.add(payment)

    # Vaciar carrito
    for ci in list(cart.items):
        db.delete(ci)

    db.commit()
    db.refresh(order)
    return order
