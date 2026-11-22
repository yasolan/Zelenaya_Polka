import os
import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from app.auth_utils import roles_required
from app.catalog_data import CATALOG_CATEGORIES, CATEGORY_IDS
from app.stock import DEFAULT_STOCK_QTY
from app.extensions import db
from app.models import COURIER_ASSIGNABLE_STATUSES, ORDER_STATUSES, Courier, Order, Product
from app.orders_service import advance_status, assign_courier

admin_bp = Blueprint("admin", __name__)

PRODUCT_UNITS = ("кг", "шт", "пучок", "г")
ALLOWED_IMAGE_EXT = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def _parse_product_form(form):
    name = (form.get("name") or "").strip()
    description = (form.get("description") or "").strip()
    category = (form.get("category") or "").strip()
    unit = (form.get("unit") or "кг").strip()
    emoji = (form.get("emoji") or "🥬").strip()[:8]
    price_raw = (form.get("price") or "").strip().replace(",", ".")
    stock_raw = (form.get("stock_qty") or "").strip().replace(",", ".")
    image_path = (form.get("image") or "").strip()

    errors = []
    if not name:
        errors.append("Укажите название.")
    elif len(name) > 120:
        errors.append("Название слишком длинное.")
    if category not in CATEGORY_IDS:
        errors.append("Выберите категорию.")
    if unit not in PRODUCT_UNITS:
        errors.append("Недопустимая единица.")
    try:
        price = float(price_raw)
        if price <= 0:
            raise ValueError
    except ValueError:
        errors.append("Цена должна быть положительным числом.")
        price = None
    try:
        stock_qty = float(stock_raw)
        if stock_qty < 0:
            raise ValueError
    except ValueError:
        errors.append("Остаток на складе — число от 0.")
        stock_qty = None
    if description and len(description) > 500:
        errors.append("Описание слишком длинное.")
    if image_path and not re.match(r"^img/products/[a-zA-Z0-9._-]+$", image_path):
        errors.append("Путь к фото: img/products/имя-файла.jpg")

    return {
        "name": name,
        "description": description,
        "category": category,
        "unit": unit,
        "emoji": emoji or "🥬",
        "price": price,
        "stock_qty": stock_qty if stock_qty is not None else stock_raw,
        "errors": errors,
    }


def _save_uploaded_image(file_storage, product_id: int) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return ""
    if ext == ".jpeg":
        ext = ".jpg"
    filename = secure_filename(f"product-{product_id}{ext}")
    folder = os.path.join(current_app.static_folder, "img", "products")
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"img/products/{filename}"

@admin_bp.route("/")
@roles_required("admin")
def dashboard():
    status = request.args.get("status", "")
    q = Order.query.order_by(Order.created_at.desc())
    if status:
        q = q.filter_by(status=status)
    orders = q.limit(100).all()
    couriers = Courier.query.filter_by(is_active=True).all()
    return render_template(
        "admin/dashboard.html",
        orders=orders,
        couriers=couriers,
        statuses=ORDER_STATUSES,
        filter_status=status,
        assignable_statuses=COURIER_ASSIGNABLE_STATUSES,
        admin_tab="orders",
    )

@admin_bp.route("/order/<int:order_id>/status", methods=["POST"])
@roles_required("admin")
def set_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "")
    courier_raw = request.form.get("courier_id", "").strip()

    if courier_raw:
        cid = int(courier_raw)
        if order.status in COURIER_ASSIGNABLE_STATUSES:
            assign_courier(order, cid)
        else:
            flash("Курьера нельзя назначить на завершённом заказе.", "error")
            return redirect(
                url_for("admin.dashboard", status=request.args.get("return_status", ""))
            )

    if new_status and new_status != order.status:
        advance_status(order, new_status, note="Изменено диспетчером")

    return redirect(url_for("admin.dashboard", status=request.args.get("return_status", "")))


@admin_bp.route("/order/<int:order_id>/assign", methods=["POST"])
@roles_required("admin")
def assign_only(order_id):
    order = Order.query.get_or_404(order_id)
    courier_raw = request.form.get("courier_id", "").strip()
    if not courier_raw:
        flash("Выберите курьера.", "error")
    elif assign_courier(order, int(courier_raw)):
        flash("Курьер назначен.", "success")
    else:
        flash("Нельзя назначить курьера для этого статуса.", "error")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/products")
@roles_required("admin")
def products():
    stock = request.args.get("stock", "")
    q = Product.query.order_by(Product.category, Product.name)
    if stock == "active":
        q = q.filter_by(is_active=True)
    elif stock == "stopped":
        q = q.filter_by(is_active=False)
    items = q.all()
    return render_template(
        "admin/products.html",
        products=items,
        categories=CATALOG_CATEGORIES,
        filter_stock=stock,
        admin_tab="products",
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@roles_required("admin")
def product_new():
    data = {
        "name": "",
        "description": "",
        "category": CATEGORY_IDS[0],
        "unit": "кг",
        "emoji": "🥬",
        "price": "",
        "stock_qty": f"{DEFAULT_STOCK_QTY:g}",
        "image": "",
        "errors": [],
    }
    if request.method == "POST":
        data = _parse_product_form(request.form)
        if not data["errors"]:
            dup = Product.query.filter_by(name=data["name"]).first()
            if dup:
                data["errors"].append("Товар с таким названием уже есть.")
            else:
                product = Product(
                    name=data["name"],
                    description=data["description"],
                    price=data["price"],
                    unit=data["unit"],
                    category=data["category"],
                    emoji=data["emoji"],
                    image=data["image"],
                    stock_qty=data["stock_qty"],
                    is_active=True,
                    catalog_managed=False,
                )
                db.session.add(product)
                db.session.flush()
                uploaded = _save_uploaded_image(request.files.get("photo"), product.id)
                if uploaded:
                    product.image = uploaded
                elif data["image"]:
                    product.image = data["image"]
                db.session.commit()
                flash("Товар добавлен в каталог.", "success")
                return redirect(url_for("admin.products"))
    return render_template(
        "admin/product_form.html",
        product=None,
        form=data,
        categories=CATALOG_CATEGORIES,
        units=PRODUCT_UNITS,
        admin_tab="products",
    )


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@roles_required("admin")
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    data = {
        "name": product.name,
        "description": product.description or "",
        "category": product.category,
        "unit": product.unit,
        "emoji": product.emoji,
        "price": f"{float(product.price):.2f}".rstrip("0").rstrip("."),
        "stock_qty": f"{float(product.stock_qty):g}",
        "image": product.image or "",
        "errors": [],
    }
    if request.method == "POST":
        data = _parse_product_form(request.form)
        if not data["errors"]:
            other = Product.query.filter(
                Product.name == data["name"], Product.id != product.id
            ).first()
            if other:
                data["errors"].append("Товар с таким названием уже есть.")
            else:
                product.name = data["name"]
                product.description = data["description"]
                product.price = data["price"]
                product.unit = data["unit"]
                product.category = data["category"]
                product.emoji = data["emoji"]
                product.stock_qty = data["stock_qty"]
                uploaded = _save_uploaded_image(request.files.get("photo"), product.id)
                if uploaded:
                    product.image = uploaded
                elif data["image"]:
                    product.image = data["image"]
                db.session.commit()
                flash("Карточка сохранена.", "success")
                return redirect(url_for("admin.products"))
    return render_template(
        "admin/product_form.html",
        product=product,
        form=data,
        categories=CATALOG_CATEGORIES,
        units=PRODUCT_UNITS,
        admin_tab="products",
    )


@admin_bp.route("/products/<int:product_id>/stock", methods=["POST"])
@roles_required("admin")
def product_set_stock(product_id):
    product = Product.query.get_or_404(product_id)
    raw = (request.form.get("stock_qty") or "").strip().replace(",", ".")
    try:
        qty = float(raw)
        if qty < 0:
            raise ValueError
    except ValueError:
        flash("Укажите корректный остаток (0 или больше).", "error")
    else:
        product.stock_qty = round(qty, 2)
        db.session.commit()
        flash(f"Остаток «{product.name}»: {product.stock_label()}.", "success")
    return redirect(
        url_for("admin.products", stock=request.args.get("return_stock", ""))
    )


@admin_bp.route("/products/<int:product_id>/toggle-active", methods=["POST"])
@roles_required("admin")
def product_toggle_active(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    if product.is_active:
        flash(f"«{product.name}» снова в продаже.", "success")
    else:
        flash(f"«{product.name}» в стоп-листе (скрыт из каталога).", "success")
    return redirect(
        url_for("admin.products", stock=request.args.get("return_stock", ""))
    )