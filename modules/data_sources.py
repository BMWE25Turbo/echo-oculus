from __future__ import annotations
from typing import Dict, Any, List
from hashlib import md5

from modules.constants import SOURCE_WEIGHTS, MIN_CONFIDENCE
from modules.utils import log_event
from modules import waze, reddit, twitter, scanner


def _key(r: Dict[str, Any]) -> str:
    norm = (
        str(round(r.get("lat", 0.0), 5)),
        str(round(r.get("lon", 0.0), 5)),
        r.get("type", ""),
        (r.get("msg") or "")[:64],
        r.get("source", ""),
    )
    return md5("|".join(norm).encode("utf-8")).hexdigest()


def _dedupe(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for r in reports:
        k = _key(r)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


class DataSources:
    """Merge Tier-1/2 public feeds, dedupe, basic weights."""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.eo = (cfg.get("echo_oculus") or {})
        self.feeds = (self.eo.get("feeds") or {})

    def get_all_reports(self, location: Dict[str, float] | None) -> List[Dict[str, Any]]:
        reports: List[Dict[str, Any]] = []

        if self.feeds.get("waze", True):
            try:
                reports += waze.get_reports(location)
            except Exception as e:
                log_event("waze_fetch_failed", {"error": str(e)}, level="WARNING")

        if self.feeds.get("reddit", True):
            try:
                reports += reddit.get_reports(location)
            except Exception as e:
                log_event("reddit_fetch_failed", {"error": str(e)}, level="WARNING")

        if self.feeds.get("twitter", True):
            try:
                reports += twitter.get_reports(location)
            except Exception as e:
                log_event("twitter_fetch_failed", {"error": str(e)}, level="WARNING")

        if self.feeds.get("scanner", "optional"):
            try:
                reports += scanner.get_reports(location)
            except Exception as e:
                log_event("scanner_json_failed", {"error": str(e)}, level="WARNING")

        for r in reports:
            w = SOURCE_WEIGHTS.get(r.get("source", ""), 0.5)
            r["confidence"] = max(MIN_CONFIDENCE, float(r.get("confidence", 0.5)) * w)

        return _dedupe(reports)
