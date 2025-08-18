# Optional: alternate reddit path via RSS if you want to use it later.
from __future__ import annotations
from typing import Dict, Any, List
import requests

def fetch_rss(sub: str) -> List[Dict[str, Any]]:
    url = f"https://www.reddit.com/{sub}/.rss"
    r = requests.get(url, timeout=6, headers={"User-Agent": "echo-oculus/0.1"})
    if r.status_code != 200:
        return []
    # parse later if needed
    return []
