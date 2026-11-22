from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

USER_ROLES = ("user", "picker", "courier", "admin")


ORDER_STATUSES = [
    ("new", "Создан"),
    ("confirmed", "Подтверждён"),
    ("picking", "Собираем"),
    ("assigned", "Передан курьеру"),
    ("on_the_way", "В пути"),
    ("delivered", "Доставлен"),
    ("cancelled", "Отменён"),
]

STATUS_ORDER = [s[0] for s in ORDER_STATUSES]
COURIER_ETA_MINUTES = 30
COURIER_ASSIGNABLE_STATUSES = frozenset(
    {"new", "confirmed", "picking", "assigned", "on_the_way"}
)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), default="")
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(32), default="кг")
    category = db.Column(db.String(64), default="овощи")
    emoji = db.Column(db.String(8), default="🥬")
    image = db.Column(db.String(200), default="")
    is_active = db.Column(db.Boolean, default=True)
    catalog_managed = db.Column(db.Boolean, default=True)
    stock_qty = db.Column(db.Numeric(10, 2), nullable=False, default=100)

    def price_rub(self):
        return f"{float(self.price):.0f} ₽"

    def sell_step(self) -> float:
        if self.unit in ("шт", "пучок", "г"):
            return 1.0
        return 0.5

    def sell_min(self) -> float:
        return self.sell_step()

    def sell_default_qty(self) -> float:
        return self.sell_min()

    def stock_amount(self) -> float:
        return float(self.stock_qty or 0)

    def is_in_stock(self) -> bool:
        return self.stock_amount() >= self.sell_min() - 1e-9

    def is_for_sale(self) -> bool:
        return bool(self.is_active) and self.is_in_stock()

    def stock_label(self) -> str:
        n = self.stock_amount()
        if abs(n - round(n)) < 1e-6:
            return f"{int(round(n))} {self.unit}"
        return f"{n:g} {self.unit}"

    def max_order_qty(self) -> float:
        from app.stock import max_valid_cart_qty

        return max_valid_cart_qty(self)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    public_code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    entrance = db.Column(db.String(16), default="")
    floor = db.Column(db.String(16), default="")
    apartment = db.Column(db.String(16), default="")
    intercom = db.Column(db.String(32), default="")
    delivery_lat = db.Column(db.Float, nullable=True)
    delivery_lon = db.Column(db.Float, nullable=True)
    comment = db.Column(db.String(500), default="")
    status = db.Column(db.String(32), default="new", nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey("couriers.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete")
    status_history = db.relationship(
        "OrderStatusEvent",
        back_populates="order",
        cascade="all, delete",
        order_by="OrderStatusEvent.created_at",
    )
    courier = db.relationship("Courier", back_populates="orders")
    customer = db.relationship("User", back_populates="orders")

    def status_label(self):
        for code, label in ORDER_STATUSES:
            if code == self.status:
                return label
        return self.status

    def total(self):
        return sum(float(i.line_total()) for i in self.items)

    def status_was_reached(self, step: str) -> bool:
        if self.status == step:
            return True
        return any(ev.status == step for ev in self.status_history)

    def delivery_details_parts(self):
        parts = []
        if self.entrance:
            parts.append(f"подъезд {self.entrance}")
        if self.floor:
            parts.append(f"этаж {self.floor}")
        if self.apartment:
            parts.append(f"кв. {self.apartment}")
        if self.intercom:
            parts.append(f"домофон {self.intercom}")
        return parts

    def delivery_summary(self):
        details = ", ".join(self.delivery_details_parts())
        if details:
            return f"{self.address} ({details})"
        return self.address

    def courier_timer_started_at(self):
        """Старт 30 мин — когда курьер нажал «Взял заказ» (статус on_the_way)."""
        if self.status != "on_the_way":
            return None
        for ev in sorted(self.status_history, key=lambda e: e.created_at):
            if ev.status == "on_the_way":
                return ev.created_at
        return None

    def courier_eta_deadline(self):
        started = self.courier_timer_started_at()
        if not started:
            return None
        return started + timedelta(minutes=COURIER_ETA_MINUTES)

    def show_courier_eta(self):
        return self.courier_eta_deadline() is not None


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    price_at_order = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    def line_total(self):
        return float(self.quantity) * float(self.price_at_order)


class OrderStatusEvent(db.Model):
    __tablename__ = "order_status_events"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    note = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", back_populates="status_history")

    def status_label(self):
        for code, label in ORDER_STATUSES:
            if code == self.status:
                return label
        return self.status


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="user")
    display_name = db.Column(db.String(120), default="")
    courier_id = db.Column(db.Integer, db.ForeignKey("couriers.id"), nullable=True)
    phone = db.Column(db.String(32), default="")

    courier = db.relationship("Courier", back_populates="user_account")
    addresses = db.relationship(
        "UserAddress", back_populates="user", cascade="all, delete-orphan"
    )
    orders = db.relationship("Order", back_populates="customer")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class UserAddress(db.Model):
    __tablename__ = "user_addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(80), default="Дом")
    address = db.Column(db.String(300), nullable=False)
    entrance = db.Column(db.String(16), default="")
    floor = db.Column(db.String(16), default="")
    apartment = db.Column(db.String(16), default="")
    intercom = db.Column(db.String(32), default="")
    delivery_lat = db.Column(db.Float, nullable=True)
    delivery_lon = db.Column(db.Float, nullable=True)
    is_default = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="addresses")


class Courier(db.Model):
    __tablename__ = "couriers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), default="")
    is_active = db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", back_populates="courier")
    user_account = db.relationship("User", back_populates="courier", uselist=False)
