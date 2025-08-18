from __future__ import annotations
import json
import os
from typing import Optional, Dict, Any

from modules.utils import log_event


class GPSLogger:
    """
    Phase 1: simple location provider.
    - mode 'mock' reads from env or mock file.
    - mode 'owntracks' placeholder (upgrade to MQTT later; main.py unchanged).
    """
    def __init__(self, cfg: Dict[str, Any]):
        eo = (cfg.get("echo_oculus") or {})
        self.mode = (eo.get("gps_device") or "mock").lower()
        self._last = None  # type: Optional[Dict[str, float]]

    def get_location(self) -> Optional[Dict[str, float]]:
        if self.mode == "mock":
            try:
                lat = float(os.environ.get("EO_MOCK_LAT", "45.5152"))
                lon = float(os.environ.get("EO_MOCK_LON", "-122.6784"))
                self._last = {"lat": lat, "lon": lon}
            except Exception:
                pass
            return self._last

        if self.mode == "owntracks":
            if not self._last:
                try:
                    with open("last_location.json", "r") as f:
                        self._last = json.load(f)
                except Exception:
                    self._last = {"lat": 45.5152, "lon": -122.6784}
            return self._last

        log_event("GPS mode unsupported", {"mode": self.mode}, level="WARNING")
        return self._last
