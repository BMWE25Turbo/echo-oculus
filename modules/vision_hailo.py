# Phase 3+ stub interface to Hailo-8L pipelines.
# No faces/plates; only hazards/objects meta returned.
from __future__ import annotations
from typing import Dict, Any, List

def detect_hazards(frame_bytes: bytes) -> List[Dict[str, Any]]:
    # placeholder
    return []
