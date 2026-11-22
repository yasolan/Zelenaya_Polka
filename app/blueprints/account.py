from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.auth_utils import roles_required
from app.extensions import db
from app.models import UserAddress

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/addresses", methods=["GET", "POST"])
@login_required
@roles_required("user", "admin")
def addresses():
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "delete":
            addr_id = int(request.form.get("address_id", 0))
            addr = UserAddress.query.filter_by(
                id=addr_id, user_id=current_user.id
            ).first_or_404()
            db.session.delete(addr)
            db.session.commit()
            flash("Адрес удалён.", "success")
        else:
            addr = UserAddress(
                user_id=current_user.id,
                title=request.form.get("title", "Дом").strip() or "Дом",
                address=request.form.get("address", "").strip(),
                entrance=request.form.get("entrance", "").strip(),
                floor=request.form.get("floor", "").strip(),
                apartment=request.form.get("apartment", "").strip(),
                intercom=request.form.get("intercom", "").strip(),
                delivery_lat=_float_or_none(request.form.get("delivery_lat")),
                delivery_lon=_float_or_none(request.form.get("delivery_lon")),
                is_default=bool(request.form.get("is_default")),
            )
            if not addr.address:
                flash("Укажите адрес.", "error")
            else:
                if addr.is_default:
                    UserAddress.query.filter_by(user_id=current_user.id).update(
                        {"is_default": False}
                    )
                db.session.add(addr)
                db.session.commit()
                flash("Адрес сохранён.", "success")
        return redirect(url_for("account.addresses"))

    items = (
        UserAddress.query.filter_by(user_id=current_user.id)
        .order_by(UserAddress.is_default.desc(), UserAddress.id.desc())
        .all()
    )
    return render_template("account/addresses.html", addresses=items)


def _float_or_none(raw):
    raw = (raw or "").strip()
    return float(raw) if raw else None
