"""Проверка точки внутри зоны доставки (полигон из конструктора 2ГИС)."""


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray casting. ring: [[lon, lat], ...] — замкнутый контур."""
    if len(ring) < 3:
        return True

    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_delivery_zone(lon: float, lat: float, zone: list[list[float]] | None) -> bool:
    if not zone:
        return True
    return point_in_ring(lon, lat, zone)
