from __future__ import annotations
from typing import Dict, Any, List
import requests

from modules.constants import SCANNER_JSON_FEEDS
from modules.utils import log_event


def get_reports(location: Dict[str, float] | None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for url in SCANNER_JSON_FEEDS:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                continue
            payload = r.json() or {}
            # Expect schema: [{msg, lat, lon, type, confidence}]
            for item in payload if isinstance(payload, list) else []:
                results.append({
                    "source": "scanner-json",
                    "type": item.get("type", "police"),
                    "msg": (item.get("msg") or "")[:200],
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "confidence": float(item.get("confidence", 0.6)),
                })
        except Exception as e:
            log_event("scanner_json_error", {"url": url, "error": str(e)}, level="WARNING")
    return results
