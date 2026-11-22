from flask import Blueprint, redirect, render_template, request, url_for

from app.auth_utils import roles_required
from app.models import ORDER_STATUSES, Order
from app.orders_service import advance_status

picker_bp = Blueprint("picker", __name__, url_prefix="/picker")

PICKER_STATUSES = ("new", "confirmed", "picking")
PICKER_NEXT = {
    "new": "confirmed",
    "confirmed": "picking",
    "picking": "assigned",
}


@picker_bp.route("/")
@roles_required("picker", "admin")
def dashboard():
    status = request.args.get("status", "")
    q = Order.query.filter(Order.status.in_(PICKER_STATUSES + ("assigned",)))
    if status in PICKER_STATUSES:
        q = q.filter_by(status=status)
    orders = q.order_by(Order.created_at.desc()).limit(100).all()
    return render_template(
        "picker/dashboard.html",
        orders=orders,
        statuses=ORDER_STATUSES,
        picker_statuses=PICKER_STATUSES,
        filter_status=status,
    )


@picker_bp.route("/order/<int:order_id>/advance", methods=["POST"])
@roles_required("picker", "admin")
def advance(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status not in PICKER_STATUSES:
        return redirect(url_for("picker.dashboard"))
    nxt = PICKER_NEXT.get(order.status)
    if nxt:
        note = "Сборщик обновил статус"
        if nxt == "assigned":
            note = "Сборка завершена, готов к передаче курьеру"
        advance_status(order, nxt, note=note)
    return redirect(url_for("picker.dashboard"))
