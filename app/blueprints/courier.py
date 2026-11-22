from flask import Blueprint, redirect, render_template, url_for

from app.auth_utils import roles_required
from app.models import Order
from app.orders_service import advance_status

courier_bp = Blueprint("courier", __name__)


def _courier_filter(query):
    from flask_login import current_user

    if current_user.role == "courier" and current_user.courier_id:
        return query.filter_by(courier_id=current_user.courier_id)
    if current_user.role == "admin":
        return query
    return query.filter_by(id=-1)


@courier_bp.route("/")
@roles_required("courier", "admin")
def home():
    q = _courier_filter(Order.query).filter(
        Order.status.in_(["confirmed", "picking", "assigned", "on_the_way"])
    )
    orders = q.order_by(Order.updated_at.desc()).all()
    return render_template("courier/orders.html", orders=orders)


@courier_bp.route("/order/<int:order_id>/advance", methods=["POST"])
@roles_required("courier", "admin")
def advance(order_id):
    from flask_login import current_user

    order = Order.query.get_or_404(order_id)
    if current_user.role == "courier" and order.courier_id != current_user.courier_id:
        return redirect(url_for("courier.home"))
    if order.status == "assigned":
        advance_status(order, "on_the_way", note="Курьер взял заказ")
    elif order.status == "on_the_way":
        advance_status(order, "delivered", note="Заказ доставлен")
    return redirect(url_for("courier.home"))
