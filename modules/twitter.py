from __future__ import annotations
from typing import Dict, Any, List
import requests
from modules.constants import TWITTER_QUERY_TAGS
from modules.utils import log_event

UA = {"User-Agent": "echo-oculus/0.1 (news-proxy)"}


def get_reports(location: Dict[str, float] | None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for tag in TWITTER_QUERY_TAGS:
        try:
            # Use Google News JSON endpoint via gnews free mirror pattern (safe/ToS-aware)
            url = f"https://gnews.io/api/v4/search?q={tag}&max=10&token=demo"
            r = requests.get(url, headers=UA, timeout=6)
            if r.status_code == 200:
                data = r.json() or {}
                for art in data.get("articles", []):
                    title = (art.get("title") or "")[:180]
                    if not title:
                        continue
                    results.append({
                        "source": "twitter-news",
                        "type": "police",
                        "msg": title,
                        "lat": None, "lon": None,
                        "confidence": 0.55,
                    })
        except Exception as e:
            log_event("twitter_proxy_error", {"tag": tag, "error": str(e)}, level="WARNING")
    return results
