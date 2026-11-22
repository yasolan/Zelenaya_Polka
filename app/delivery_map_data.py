"""Данные карты: зона и магазины, извлечённые из виджета 2ГИС (конструктор)."""

from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

from flask import current_app

DATA_PATH = Path(__file__).resolve().parent / "static" / "data" / "delivery-map.json"


def _decode_widget_url(url: str) -> dict:
    match = re.search(r"data=([^&]+)", url)
    if not match:
        raise ValueError("В DGIS_MAP_WIDGET_URL нет параметра data")
    raw_b64 = match.group(1)
    pad = "=" * (-len(raw_b64) % 4)
    payload = zlib.decompress(base64.urlsafe_b64decode(raw_b64 + pad))
    return json.loads(payload)


def build_map_payload(widget_url: str) -> dict:
    doc = _decode_widget_url(widget_url)
    zone_ring: list[list[float]] | None = None
    stores: list[dict] = []

    for feature in doc.get("orderedGeometries", []):
        geom = feature.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates") or []
        props = feature.get("properties") or {}

        if gtype == "LineString" and len(coords) >= 3:
            zone_ring = [[float(lon), float(lat)] for lon, lat in coords]

        if gtype == "Point" and len(coords) == 2:
            lon, lat = float(coords[0]), float(coords[1])
            title_b64 = props.get("title")
            name = "Зелёная полка"
            if title_b64:
                try:
                    name = base64.b64decode(title_b64).decode("utf-8")
                except (ValueError, UnicodeDecodeError):
                    pass
            stores.append(
                {
                    "name": name,
                    "address": props.get("address") or "",
                    "lon": lon,
                    "lat": lat,
                }
            )

    # Координаты из конструктора 2ГИС → фактические адреса пунктов
    address_fix = {
        (39.91642534732819, 59.2168078989861): "г. Вологда, ул. Прокатова, 4",
        (39.92369413375855, 59.204758693713295): "г. Вологда, Советский проспект, 148",
        (39.85311448574067, 59.213785013522944): "г. Вологда, ул. Ленинградская, 76А",
    }
    for store in stores:
        key = (store["lon"], store["lat"])
        if key in address_fix:
            store["address"] = address_fix[key]
            store["name"] = f"Зелёная полка — {address_fix[key].split(', ', 1)[-1]}"
        if not store.get("address"):
            store["address"] = f"{store['lat']:.5f}, {store['lon']:.5f}"

    pos = doc.get("mapPosition") or {}
    return {
        "center": {
            "lat": float(pos.get("lat", 59.217)),
            "lon": float(pos.get("lon", 39.920)),
            "zoom": int(pos.get("zoom", 12)),
        },
        "zone": zone_ring,
        "stores": stores,
    }


def refresh_map_data_file() -> dict:
    url = current_app.config["DGIS_MAP_WIDGET_URL"]
    payload = build_map_payload(url)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def load_map_data() -> dict:
    url = current_app.config.get("DGIS_MAP_WIDGET_URL", "")
    if url:
        try:
            return build_map_payload(url)
        except (ValueError, zlib.error, json.JSONDecodeError, KeyError):
            pass
    if DATA_PATH.is_file():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {
        "center": {"lat": 59.217, "lon": 39.920, "zoom": 12},
        "zone": [],
        "stores": [],
    }
