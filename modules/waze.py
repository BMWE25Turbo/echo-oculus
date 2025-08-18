# modules/waze.py
from __future__ import annotations
import requests
from typing import List, Dict, Any

from .utils import log_event
from .constants import (
    WAZE_API_URL,                   # your original name
)
# Back-compat alias if code elsewhere expects WAZE_FEED_URL
WAZE_FEED_URL = WAZE_API_URL

# Waze sometimes classifies police as "POLICE" or "POLICE_VISIBLE" etc.
_POLICE_TYPES = {"POLICE", "POLICE_VISIBLE", "POLICE_HIDING", "POLICE_ACCIDENT"}

# normalize → EO report envelope
def _mk_report(a: Dict[str, Any]) -> Dict[str, Any]:
    # Waze alert fields are not guaranteed; be defensive
    lat = a.get("location", {}).get("y") or a.get("y") or a.get("latitude")
    lon = a.get("location", {}).get("x") or a.get("x") or a.get("longitude")
    conf = float(a.get("reliability", 6)) / 10.0  # rough 0..1
    msg = a.get("subtype") or a.get("type") or "police"
    return {
        "source": "waze",
        "type": "police",
        "lat": lat,
        "lon": lon,
        "confidence": max(0.0, min(1.0, conf)),
        "message": msg,
        "raw": {"id": a.get("uuid") or a.get("id")},
    }

def fetch_waze_alerts(timeout_s: int = 6) -> List[Dict[str, Any]]:
    """
    Pull Waze GeoRSS/JSON and return **police-only** alerts normalized for EO.
    Safe defaults, short timeout, and defensive parsing.
    """
    try:
        r = requests.get(
            WAZE_FEED_URL,
            headers={"User-Agent": "echo-oculus/1.0"},
            timeout=timeout_s,
        )
        if r.status_code != 200:
            log_event("Waze fetch failed", {"status": r.status_code}, level="WARNING")
            return []

        data = r.json() if r.headers.get("Content-Type", "").startswith("application/json") else {}
        alerts = (data.get("alerts") or []) if isinstance(data, dict) else []

        police = [a for a in alerts if (a.get("type") in _POLICE_TYPES)]
        reports = [_mk_report(a) for a in police if a]

        log_event("Fetched Waze police alerts", {"count": len(reports)})
        return reports
    except Exception as e:
        log_event("Exception during Waze fetch", {"error": str(e)}, level="ERROR")
        return []
