from flask import Flask

from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.blueprints.shop import shop_bp
    from app.blueprints.orders import orders_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.courier import courier_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.account import account_bp
    from app.blueprints.picker import picker_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(courier_bp, url_prefix="/courier")
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(picker_bp)

    from app.auth_utils import nav_visibility
    from app.cart import cart_count, get_cart
    from app.catalog_data import CATALOG_CATEGORIES

    @app.context_processor
    def inject_nav():
        return {"nav": nav_visibility()}

    @app.context_processor
    def inject_cart_globals():
        cart = get_cart()
        quantities = {int(pid): float(qty) for pid, qty in cart.items()}
        return {
            "cart_count": cart_count(),
            "catalog_categories": CATALOG_CATEGORIES,
            "cart_quantities": quantities,
        }

    from app.timezone_util import format_display_dt, utc_iso_z

    @app.template_filter("minsk_time")
    def minsk_time_filter(value, fmt="%d.%m.%Y %H:%M"):
        return format_display_dt(value, fmt)

    @app.template_filter("qty_format")
    def qty_format_filter(value):
        n = float(value)
        if abs(n - round(n)) < 1e-6:
            return str(int(round(n)))
        return f"{n:.1f}".replace(".", ",")

    app.jinja_env.globals["utc_iso_z"] = utc_iso_z

    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
        from app.db_migrate import ensure_schema

        ensure_schema()
        from app.seed import seed_if_empty, sync_catalog_products
        from app.seed_users import seed_users

        seed_if_empty()
        sync_catalog_products()
        seed_users()

    return app
