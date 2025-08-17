import yaml
import logging
import json
import math
import os
from datetime import datetime, timezone


# --- Config ---
def load_config(path: str):
    """Load YAML config from disk."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


# --- Logging helper used across modules (non-destructive addition) ---
def log_event(msg: str, meta: dict | None = None, level: str = "INFO"):
    """
    Lightweight structured logger used by multiple modules.
    Keeps your existing text logs but allows key/value context.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)
    try:
        payload = json.dumps(meta, ensure_ascii=False) if meta is not None else ""
    except Exception:
        payload = str(meta)
    logging.log(lvl, f"{msg}{' :: ' + payload if payload else ''}")


# --- Time helpers (for consistent timestamps) ---
def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


# --- Geo helpers (reuse anywhere, Phase 3/5 ready) ---
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def mi_to_m(mi: float) -> float:
    return mi * 1609.344


# --- FS helper (used by logging/retention, safe no-op if exists) ---
def ensure_dir(path: str):
    if path and not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
