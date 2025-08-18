from __future__ import annotations
from typing import Dict, Any, List

def heat_zone_score(location: Dict[str, float] | None, recent_events: List[Dict[str, Any]]) -> float:
    """Stub ML scoring: later replace with trained model. Return 0..1."""
    if not recent_events:
        return 0.1
    # naive: more events -> hotter
    n = min(10, len(recent_events))
    return round(0.1 + 0.08 * n, 2)
