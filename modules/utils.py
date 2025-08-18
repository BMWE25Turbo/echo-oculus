import logging
import math
import os
import yaml
from datetime import datetime, timezone
from typing import Any, Dict


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def miles_to_meters(mi: float) -> float:
    return mi * 1609.344


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def log_event(event: str, data: Dict[str, Any] | None = None, level: str = "INFO"):
    """Uniform logging hook used across modules."""
    log = logging.getLogger(event)
    msg = {"ts": now_utc_iso(), "event": event, **(data or {})}
    lvl = getattr(logging, level.upper(), logging.INFO)
    log.log(lvl, "%s", msg)


def getenv_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}
