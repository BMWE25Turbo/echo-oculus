from __future__ import annotations
from typing import Dict, Any

def basic_tire_advice(ambient_f: float) -> str:
    if ambient_f <= 32:
        return "Check tire pressure (cold weather drops PSI)."
    if ambient_f >= 95:
        return "High heat: consider slightly lower sustained speeds; check PSI."
    return "Tire pressure OK for typical temps."
