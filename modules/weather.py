from __future__ import annotations
from typing import Dict, Any, Optional
import requests
from modules.utils import log_event

# Simple Open-Meteo wrapper (no API key)
def get_weather(lat: float, lon: float, units: str = "imperial") -> Optional[Dict[str, Any]]:
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&temperature_unit={'fahrenheit' if units=='imperial' else 'celsius'}"
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        log_event("weather_error", {"error": str(e)}, level="WARNING")
        return None
