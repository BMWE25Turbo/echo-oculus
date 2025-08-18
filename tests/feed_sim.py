# Quick smoke test for cooldown/radius.
from modules.alert_engine import AlertEngine
from modules.utils import load_config

cfg = load_config("config.yaml")
eng = AlertEngine(cfg)

loc = {"lat": 45.52, "lon": -122.68}
reports = [
    {"source": "scanner-json", "type": "police", "msg": "speed trap", "lat": 45.521, "lon": -122.680, "confidence": 0.9},
    {"source": "reddit", "type": "police", "msg": "cop near main", "lat": 45.530, "lon": -122.681, "confidence": 0.6},
]
eng.process(loc, reports)
print("OK")
