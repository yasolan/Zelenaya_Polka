from sqlalchemy import inspect, text

from app.extensions import db


def _ensure_columns(table: str, columns: list[tuple[str, str]]):
    insp = inspect(db.engine)
    if table not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns(table)}
    alters = [f"ADD COLUMN {name} {ddl}" for name, ddl in columns if name not in existing]
    if not alters:
        return
    with db.engine.begin() as conn:
        for clause in alters:
            conn.execute(text(f"ALTER TABLE {table} {clause}"))


def ensure_order_geo_columns():
    _ensure_columns(
        "orders",
        [
            ("delivery_lat", "FLOAT"),
            ("delivery_lon", "FLOAT"),
            ("entrance", "VARCHAR(16) DEFAULT ''"),
            ("floor", "VARCHAR(16) DEFAULT ''"),
            ("apartment", "VARCHAR(16) DEFAULT ''"),
            ("intercom", "VARCHAR(32) DEFAULT ''"),
            ("user_id", "INTEGER"),
        ],
    )


def ensure_product_columns():
    _ensure_columns(
        "products",
        [
            ("image", "VARCHAR(200) DEFAULT ''"),
            ("catalog_managed", "BOOLEAN DEFAULT 1 NOT NULL"),
            ("stock_qty", "NUMERIC(10, 2) DEFAULT 100 NOT NULL"),
        ],
    )


def ensure_schema():
    ensure_order_geo_columns()
    ensure_product_columns()
