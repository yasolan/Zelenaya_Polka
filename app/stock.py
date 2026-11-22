"""Складские остатки: ограничение корзины, списание и возврат."""

from __future__ import annotations

from app.cart import get_cart, normalize_product_qty, set_cart_item
from app.extensions import db
from app.models import Order, Product

DEFAULT_STOCK_QTY = 100.0


def stock_float(product: Product) -> float:
    return float(product.stock_qty or 0)


def product_is_for_sale(product: Product | None) -> bool:
    if not product or not product.is_active:
        return False
    return stock_float(product) >= product.sell_min() - 1e-9


def max_valid_cart_qty(product: Product) -> float:
    """Максимальное количество с учётом шага продажи и остатка на складе."""
    cap = stock_float(product)
    step = product.sell_step()
    min_qty = product.sell_min()
    if cap < min_qty - 1e-9:
        return 0.0
    steps = int((cap - min_qty) // step + 1e-9)
    return round(min_qty + steps * step, 3)


def clamp_cart_qty(product: Product, qty: float) -> float:
    qty = normalize_product_qty(qty, product.sell_step(), product.sell_min())
    if qty <= 0:
        return 0.0
    limit = max_valid_cart_qty(product)
    if limit <= 0:
        return 0.0
    if qty > limit + 1e-9:
        return limit
    return qty


def sanitize_session_cart():
    """Подогнать корзину под актуальные остатки (после админских правок)."""
    cart = get_cart()
    if not cart:
        return
    for pid_str, qty in list(cart.items()):
        product = Product.query.get(int(pid_str))
        if not product_is_for_sale(product):
            set_cart_item(int(pid_str), 0)
            continue
        capped = clamp_cart_qty(product, float(qty))
        if abs(capped - float(qty)) > 1e-9:
            set_cart_item(int(pid_str), capped)


def validate_cart_stock(cart: dict) -> list[str]:
    errors = []
    for pid_str, qty in cart.items():
        product = Product.query.get(int(pid_str))
        if not product or not product.is_active:
            errors.append("В корзине есть недоступный товар.")
            continue
        need = float(qty)
        if need <= 0:
            continue
        limit = max_valid_cart_qty(product)
        if need > limit + 1e-9:
            unit = product.unit
            errors.append(
                f"«{product.name}»: на складе {limit:g} {unit}, в корзине {need:g} {unit}."
            )
        elif need < product.sell_min() - 1e-9:
            errors.append(f"«{product.name}»: минимальный заказ {product.sell_min():g} {product.unit}.")
    return errors


def deduct_stock_for_order(order: Order):
    for item in order.items:
        product = item.product
        if not product:
            continue
        product.stock_qty = round(stock_float(product) - float(item.quantity), 3)


def restore_stock_for_order(order: Order):
    for item in order.items:
        product = item.product
        if not product:
            continue
        product.stock_qty = round(stock_float(product) + float(item.quantity), 3)


def commit_stock_changes():
    db.session.commit()