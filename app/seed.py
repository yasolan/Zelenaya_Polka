import random
import string

from app.catalog_data import PRODUCTS, PRODUCT_IMAGES
from app.stock import DEFAULT_STOCK_QTY
from app.extensions import db
from app.models import Courier, Order, OrderItem, OrderStatusEvent, Product


def sync_product_images():
    updated = False
    for name, image_path in PRODUCT_IMAGES.items():
        product = Product.query.filter_by(name=name).first()
        if product and product.image != image_path:
            product.image = image_path
            updated = True
    if updated:
        db.session.commit()


def sync_catalog_products():
    """Upsert catalog rows (new items + category/image updates on existing DB)."""
    for name, description, price, unit, category, emoji, image in PRODUCTS:
        product = Product.query.filter_by(name=name).first()
        if product is None:
            db.session.add(
                Product(
                    name=name,
                    description=description,
                    price=price,
                    unit=unit,
                    category=category,
                    emoji=emoji,
                    image=image,
                    catalog_managed=True,
                    stock_qty=DEFAULT_STOCK_QTY,
                )
            )
        else:
            product.description = description
            product.price = price
            product.unit = unit
            product.category = category
            product.emoji = emoji
            product.image = image
            product.catalog_managed = True
    catalog_names = {name for name, *_ in PRODUCTS}
    stale = Product.query.filter(
        Product.catalog_managed.is_(True),
        Product.name.notin_(catalog_names),
    )
    for product in stale.all():
        product.is_active = False
    db.session.commit()
    sync_product_images()


def seed_if_empty():
    if Product.query.first():
        sync_catalog_products()
        return

    for name, description, price, unit, category, emoji, image in PRODUCTS:
        db.session.add(
            Product(
                name=name,
                description=description,
                price=price,
                unit=unit,
                category=category,
                emoji=emoji,
                image=image,
                stock_qty=DEFAULT_STOCK_QTY,
            )
        )

    db.session.add(Courier(name="Алексей Курьер", phone="+7 900 111-22-33"))
    db.session.add(Courier(name="Марина Доставка", phone="+7 900 444-55-66"))
    db.session.commit()

    demo_code = "ZP-" + "".join(random.choices(string.digits, k=6))
    order = Order(
        public_code=demo_code,
        customer_name="Демо Заказчик",
        phone="+7 900 000-00-00",
        address="г. Москва, ул. Примерная, д. 1, кв. 10",
        comment="Позвонить за 10 минут",
        status="on_the_way",
        courier_id=1,
    )
    db.session.add(order)
    db.session.flush()

    p = Product.query.filter_by(name="Томаты круглые").first()
    db.session.add(
        OrderItem(order_id=order.id, product_id=p.id, quantity=1, price_at_order=p.price)
    )
    p2 = Product.query.filter_by(name="Яблоки Гала").first()
    db.session.add(
        OrderItem(
            order_id=order.id, product_id=p2.id, quantity=2, price_at_order=p2.price
        )
    )

    for st in ("new", "confirmed", "picking", "assigned", "on_the_way"):
        db.session.add(OrderStatusEvent(order_id=order.id, status=st))

    db.session.commit()
