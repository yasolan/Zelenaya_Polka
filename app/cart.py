from flask import session


def get_cart():
    return session.setdefault("cart", {})


def cart_count():
    cart = get_cart()
    return sum(int(v) for v in cart.values())


def add_to_cart(product_id: int, quantity: float = 1):
    cart = get_cart()
    key = str(product_id)
    cart[key] = float(cart.get(key, 0)) + quantity
    session["cart"] = cart
    session.modified = True


def set_cart_item(product_id: int, quantity: float):
    cart = get_cart()
    key = str(product_id)
    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = quantity
    session["cart"] = cart
    session.modified = True


def clear_cart():
    session.pop("cart", None)
    session.modified = True


def normalize_product_qty(qty: float, step: float, min_qty: float) -> float:
    if qty < min_qty - 1e-9:
        return 0.0
    steps = round((qty - min_qty) / step)
    return round(min_qty + steps * step, 3)
