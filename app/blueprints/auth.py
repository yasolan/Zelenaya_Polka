from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user

from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_url = request.args.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(_home_for_role(user.role))
        flash("Неверный логин или пароль.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("shop.index"))


def _home_for_role(role: str):
    if role == "admin":
        return url_for("admin.dashboard")
    if role == "picker":
        return url_for("picker.dashboard")
    if role == "courier":
        return url_for("courier.home")
    return url_for("shop.index")
