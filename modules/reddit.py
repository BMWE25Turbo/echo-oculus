from __future__ import annotations
import re
from typing import Dict, Any, List
import requests

from modules.constants import REDDIT_SUBS
from modules.utils import log_event

UA = {"User-Agent": "echo-oculus/0.1 (public-rss-only)"}


def _parse_items(feed_json: Dict[str, Any], sub: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for child in (feed_json.get("data", {}) or {}).get("children", []):
        d = child.get("data", {})
        title = d.get("title", "")
        if re.search(r"\b(police|cop|speed\s*trap|checkpoint)\b", title, re.I):
            out.append({
                "source": "reddit",
                "type": "police",
                "msg": title[:180],
                "lat": None, "lon": None,
                "confidence": 0.6,
            })
    return out


def get_reports(location: Dict[str, float] | None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for sub in REDDIT_SUBS:
        try:
            url = f"https://www.reddit.com/{sub}/.json?limit=25"
            r = requests.get(url, headers=UA, timeout=6)
            if r.status_code == 200:
                results.extend(_parse_items(r.json(), sub))
        except Exception as e:
            log_event("reddit_fetch_error", {"sub": sub, "error": str(e)}, level="WARNING")
    return results
