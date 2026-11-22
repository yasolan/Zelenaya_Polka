from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import ORDER_STATUSES, Order

orders_bp = Blueprint("orders", __name__)

_INACTIVE_ORDER_STATUSES = frozenset({"delivered", "cancelled"})
_CUSTOMER_ROLES = frozenset({"user", "admin"})
_STAFF_ROLES = frozenset({"picker", "courier", "admin"})


def _orders_for_customer(active: bool):
    if not current_user.is_authenticated or current_user.role not in _CUSTOMER_ROLES:
        return []
    q = Order.query.filter_by(user_id=current_user.id)
    if active:
        q = q.filter(~Order.status.in_(_INACTIVE_ORDER_STATUSES))
    else:
        q = q.filter(Order.status.in_(_INACTIVE_ORDER_STATUSES))
    return q.order_by(Order.updated_at.desc()).limit(50).all()


def _order_for_view(code: str) -> Order | None:
    if not code or not current_user.is_authenticated:
        return None
    order = Order.query.filter_by(public_code=code).first()
    if not order:
        return None
    if current_user.role in _STAFF_ROLES:
        return order
    if current_user.role == "user":
        return order if order.user_id == current_user.id else None
    return None


@orders_bp.route("/track", methods=["GET"])
def track():
    code = request.args.get("code", "").strip().upper()
    order = _order_for_view(code) if code else None
    timeline_statuses = [(c, l) for c, l in ORDER_STATUSES if c != "cancelled"]
    show_customer_lists = (
        current_user.is_authenticated and current_user.role in _CUSTOMER_ROLES
    )
    return render_template(
        "orders/track.html",
        order=order,
        statuses=timeline_statuses,
        active_orders=_orders_for_customer(active=True) if show_customer_lists else [],
        previous_orders=_orders_for_customer(active=False) if show_customer_lists else [],
        show_customer_lists=show_customer_lists,
    )