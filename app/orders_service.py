import random
import string

from app.extensions import db
from app.models import (
    COURIER_ASSIGNABLE_STATUSES,
    Order,
    OrderItem,
    OrderStatusEvent,
    Product,
)
from app.stock import deduct_stock_for_order, restore_stock_for_order, validate_cart_stock


def generate_public_code():
    for _ in range(20):
        code = "ZP-" + "".join(random.choices(string.digits, k=6))
        if not Order.query.filter_by(public_code=code).first():
            return code
    raise RuntimeError("Could not generate unique order code")


def create_order(
    customer_name,
    phone,
    address,
    comment,
    cart: dict,
    delivery_lat=None,
    delivery_lon=None,
    entrance="",
    floor="",
    apartment="",
    intercom="",
    user_id=None,
):
    stock_errors = validate_cart_stock(cart)
    if stock_errors:
        raise ValueError(stock_errors[0])

    order = Order(
        public_code=generate_public_code(),
        customer_name=customer_name,
        phone=phone,
        address=address,
        user_id=user_id,
        entrance=entrance or "",
        floor=floor or "",
        apartment=apartment or "",
        intercom=intercom or "",
        delivery_lat=delivery_lat,
        delivery_lon=delivery_lon,
        comment=comment or "",
        status="new",
    )
    db.session.add(order)
    db.session.flush()

    for pid_str, qty in cart.items():
        product = Product.query.get(int(pid_str))
        if not product or not product.is_active:
            continue
        qty_f = float(qty)
        if qty_f <= 0:
            continue
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty_f,
                price_at_order=product.price,
            )
        )

    db.session.flush()
    deduct_stock_for_order(order)

    db.session.add(OrderStatusEvent(order_id=order.id, status="new", note="Заказ создан"))
    db.session.commit()
    return order


def advance_status(order: Order, new_status: str, note: str = ""):
    if order.status == new_status:
        return
    prev = order.status
    order.status = new_status
    if new_status == "cancelled" and prev != "cancelled":
        restore_stock_for_order(order)
    db.session.add(
        OrderStatusEvent(order_id=order.id, status=new_status, note=note or "")
    )
    db.session.commit()


def assign_courier(order: Order, courier_id: int, note: str = "Назначен курьер") -> bool:
    """Назначить курьера, не меняя статус (на любом этапе до доставки)."""
    if order.status not in COURIER_ASSIGNABLE_STATUSES:
        return False
    if order.courier_id == courier_id:
        return True
    order.courier_id = courier_id
    db.session.add(
        OrderStatusEvent(order_id=order.id, status=order.status, note=note)
    )
    db.session.commit()
    return True
