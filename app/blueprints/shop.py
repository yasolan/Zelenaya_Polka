from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.cart import add_to_cart, cart_count, clear_cart, get_cart, set_cart_item
from app.catalog_data import CATALOG_CATEGORIES, CATEGORY_IDS, CATEGORY_SORT_INDEX
from app.delivery_map_data import load_map_data
from app.extensions import db
from app.geo import point_in_delivery_zone
from app.models import Product, UserAddress
from app.orders_service import create_order
from app.stock import (
    clamp_cart_qty,
    max_valid_cart_qty,
    product_is_for_sale,
    sanitize_session_cart,
    validate_cart_stock,
)

shop_bp = Blueprint("shop", __name__)


def _saleable_products_query():
    return Product.query.filter(
        Product.is_active.is_(True),
        Product.stock_qty > 0,
    )


def _saleable_products(category: str | None = None):
    q = _saleable_products_query()
    if category:
        q = q.filter_by(category=category)
    return [p for p in q.order_by(Product.name).all() if p.is_for_sale()]


def _cart_line_items():
    cart = get_cart()
    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if not p:
            continue
        line = float(qty) * float(p.price)
        total += line
        items.append({"product": p, "quantity": float(qty), "line_total": line})
    return items, total


def _map_context(interactive: bool = False):
    data = load_map_data()
    return {
        "map_data": data,
        "map_interactive": interactive,
    }


def _checkout_context(items, total):
    saved = []
    if current_user.is_authenticated and current_user.role in ("user", "admin"):
        saved = (
            UserAddress.query.filter_by(user_id=current_user.id)
            .order_by(UserAddress.is_default.desc())
            .all()
        )
    return {
        "items": items,
        "total": total,
        "saved_addresses": saved,
        **_map_context(interactive=True),
    }


@shop_bp.route("/")
def index():
    sections = []
    for cat in CATALOG_CATEGORIES:
        products = _saleable_products(category=cat["id"])[:4]
        if products:
            sections.append({"category": cat, "products": products})
    return render_template("shop/index.html", catalog_sections=sections)


@shop_bp.route("/catalog")
def catalog():
    category = request.args.get("category", "")
    products = (
        _saleable_products(category=category)
        if category in CATEGORY_IDS
        else _saleable_products()
    )
    products.sort(
        key=lambda p: (CATEGORY_SORT_INDEX.get(p.category, 99), p.name.casefold())
    )
    category_meta = next((c for c in CATALOG_CATEGORIES if c["id"] == category), None)
    return render_template(
        "shop/catalog.html",
        products=products,
        category=category,
        category_meta=category_meta,
    )


@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    return render_template(
        "shop/product.html",
        product=product,
        out_of_stock=not product.is_in_stock(),
    )


@shop_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    product = Product.query.get(product_id)
    qty = float(request.form.get("quantity", 1) or 1)
    if not product_is_for_sale(product):
        flash("Этот товар сейчас недоступен.", "error")
    elif qty <= 0:
        flash("Укажите количество больше нуля.", "error")
    else:
        capped = clamp_cart_qty(product, qty)
        if capped <= 0:
            flash("Недостаточно товара на складе.", "error")
        else:
            add_to_cart(product_id, capped)
            if capped < qty - 1e-9:
                flash(f"Доступно не больше {capped:g} {product.unit}.", "error")
    return redirect(request.referrer or url_for("shop.catalog"))


@shop_bp.route("/cart/item/<int:product_id>", methods=["POST"])
def cart_item_api(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    if not product_is_for_sale(product):
        return jsonify(ok=False, error="out_of_stock", message="Нет на складе"), 409
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    step = product.sell_step()
    min_qty = product.sell_min()
    cart = get_cart()
    current = float(cart.get(str(product_id), 0))
    stock_max = float(max_valid_cart_qty(product))

    if action == "add":
        new_qty = min_qty
    elif action == "plus":
        new_qty = current + step if current >= min_qty else min_qty
    elif action == "minus":
        new_qty = current - step if current >= min_qty else 0.0
    elif "quantity" in payload:
        new_qty = float(payload["quantity"])
    else:
        return jsonify(ok=False, error="bad_request"), 400

    before = new_qty
    new_qty = clamp_cart_qty(product, new_qty)
    capped = before > new_qty + 1e-9 and new_qty > 0
    set_cart_item(product_id, new_qty)
    final = float(get_cart().get(str(product_id), 0))
    _, cart_total = _cart_line_items()
    line_total = float(product.price) * final if final > 0 else 0.0
    message = None
    if capped:
        message = f"На складе не больше {stock_max:g} {product.unit}."
    return jsonify(
        ok=True,
        quantity=final,
        cart_count=cart_count(),
        unit=product.unit,
        line_total=line_total,
        cart_total=cart_total,
        stock_max=stock_max,
        capped=capped,
        message=message,
    )


@shop_bp.route("/cart")
def cart_view():
    sanitize_session_cart()
    items, total = _cart_line_items()
    stock_notes = validate_cart_stock(get_cart())
    return render_template(
        "shop/cart.html", items=items, total=total, stock_notes=stock_notes
    )


@shop_bp.route("/cart/update", methods=["POST"])
def cart_update():
    for key, val in request.form.items():
        if key.startswith("qty_"):
            pid = int(key.replace("qty_", ""))
            product = Product.query.get(pid)
            if product:
                set_cart_item(pid, clamp_cart_qty(product, float(val or 0)))
            else:
                set_cart_item(pid, 0)
    return redirect(url_for("shop.cart_view"))


@shop_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()
    if not cart:
        flash("Корзина пуста.", "error")
        return redirect(url_for("shop.catalog"))

    sanitize_session_cart()
    cart = get_cart()
    items, total = _cart_line_items()

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        entrance = request.form.get("entrance", "").strip()
        floor = request.form.get("floor", "").strip()
        apartment = request.form.get("apartment", "").strip()
        intercom = request.form.get("intercom", "").strip()
        comment = request.form.get("comment", "").strip()
        lat_raw = request.form.get("delivery_lat", "").strip()
        lon_raw = request.form.get("delivery_lon", "").strip()
        delivery_lat = float(lat_raw) if lat_raw else None
        delivery_lon = float(lon_raw) if lon_raw else None
        map_data = load_map_data()
        if not name or not phone:
            flash("Заполните имя и телефон.", "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        if not address:
            flash("Выберите точку на карте — адрес определится автоматически.", "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        if delivery_lat is None or delivery_lon is None:
            flash("Укажите точку доставки на карте (клик внутри зоны).", "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        if not point_in_delivery_zone(
            delivery_lon, delivery_lat, map_data.get("zone")
        ):
            flash("Этот адрес вне зоны доставки. Выберите точку внутри контура на карте.", "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        stock_errors = validate_cart_stock(cart)
        if stock_errors:
            for err in stock_errors[:3]:
                flash(err, "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        user_id = None
        if current_user.is_authenticated and current_user.role in ("user", "admin"):
            user_id = current_user.id
            if not phone and current_user.phone:
                phone = current_user.phone
        try:
            order = create_order(
                name,
                phone,
                address,
                comment,
                cart,
                delivery_lat=delivery_lat,
                delivery_lon=delivery_lon,
                entrance=entrance,
                floor=floor,
                apartment=apartment,
                intercom=intercom,
                user_id=user_id,
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "shop/checkout.html",
                **_checkout_context(items, total),
            )
        if user_id and request.form.get("save_address"):
            _persist_address(
                user_id,
                address,
                entrance,
                floor,
                apartment,
                intercom,
                delivery_lat,
                delivery_lon,
            )
        clear_cart()
        flash(f"Заказ {order.public_code} принят!", "success")
        return redirect(url_for("orders.track", code=order.public_code))

    return render_template("shop/checkout.html", **_checkout_context(items, total))


def _persist_address(user_id, address, entrance, floor, apartment, intercom, lat, lon):
    exists = UserAddress.query.filter_by(
        user_id=user_id, address=address, apartment=apartment or ""
    ).first()
    if exists:
        return
    is_default = UserAddress.query.filter_by(user_id=user_id).count() == 0
    db.session.add(
        UserAddress(
            user_id=user_id,
            title="Дом",
            address=address,
            entrance=entrance,
            floor=floor,
            apartment=apartment,
            intercom=intercom,
            delivery_lat=lat,
            delivery_lon=lon,
            is_default=is_default,
        )
    )
    db.session.commit()


@shop_bp.route("/delivery")
def delivery_zone():
    ctx = _map_context(interactive=False)
    return render_template("shop/delivery_zone.html", **ctx)
