from __future__ import annotations
from typing import List, Dict, Any

def score_route(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Phase 3: stub scorer; later replace with real rules/model."""
    risk = sum(s.get("risk", 0.1) for s in segments) / max(1, len(segments))
    return {"risk_score": round(risk, 2), "segments": len(segments)}
