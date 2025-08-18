from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta

from modules.utils import haversine_m, miles_to_meters, log_event, now_utc_iso
from modules.constants import SOURCE_COOLDOWN_S


def _severity(conf: float, dist_m: float) -> str:
    if conf >= 0.8 and dist_m <= 1000:
        return "high"
    if conf >= 0.6 and dist_m <= 2500:
        return "medium"
    return "low"


class AlertEngine:
    """Distance filter, cooldowns, severity bucketing; emits normalized alerts."""
    def __init__(self, cfg: Dict[str, Any]):
        eo = (cfg.get("echo_oculus") or {})
        self.radius_m = miles_to_meters(float(eo.get("alert_radius_miles", 2.5)))
        self.cooldowns: Dict[str, datetime] = {}

    def _cooldown_key(self, r: Dict[str, Any]) -> str:
        return f"{r.get('source')}|{r.get('type')}|{round(r.get('lat', 0), 3)}|{round(r.get('lon', 0), 3)}"

    def _within_radius(self, loc: Dict[str, float] | None, r: Dict[str, Any]) -> float | None:
        if not loc or r.get("lat") is None or r.get("lon") is None:
            return None
        d = haversine_m(loc["lat"], loc["lon"], r["lat"], r["lon"])
        return d if d <= self.radius_m else None

    def process(self, location: Dict[str, float] | None, reports: List[Dict[str, Any]]):
        now = datetime.utcnow()
        for r in reports:
            dist_m = self._within_radius(location, r)
            if dist_m is None:
                continue

            key = self._cooldown_key(r)
            cd = SOURCE_COOLDOWN_S.get(r.get("source", ""), 900)
            until = self.cooldowns.get(key)
            if until and until > now:
                continue

            sev = _severity(float(r.get("confidence", 0.5)), dist_m)
            alert = {
                "ts": now_utc_iso(),
                "source": r.get("source"),
                "type": r.get("type", "police"),
                "msg": r.get("msg"),
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "distance_m": round(dist_m, 1),
                "confidence": round(float(r.get("confidence", 0.5)), 2),
                "severity": sev,
            }
            log_event("ALERT", alert)
            self.cooldowns[key] = now + timedelta(seconds=cd)
