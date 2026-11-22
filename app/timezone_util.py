from datetime import datetime, timedelta, timezone

DISPLAY_TZ_LABEL = "Минск"

try:
    from zoneinfo import ZoneInfo

    DISPLAY_TZ = ZoneInfo("Europe/Minsk")
except Exception:
    # Минск = UTC+3 круглый год; fallback для Windows без пакета tzdata
    DISPLAY_TZ = timezone(timedelta(hours=3))


def assume_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_display_tz(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return assume_utc(dt).astimezone(DISPLAY_TZ)


def format_display_dt(dt: datetime | None, fmt: str = "%d.%m.%Y %H:%M") -> str:
    local = to_display_tz(dt)
    return local.strftime(fmt) if local else ""


def utc_iso_z(dt: datetime | None) -> str:
    """Для JS-таймера: UTC с суффиксом Z."""
    if dt is None:
        return ""
    return assume_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")
