import requests
import json
from datetime import datetime
from modules.constants import SCANNER_FEEDS
from modules.utils import log_event

def fetch_scanner_data():
    """
    Fetches police scanner data from all defined SCANNER_FEEDS.
    Each feed should return a JSON object containing active police events.
    """
    scanner_events = []

    for feed_url in SCANNER_FEEDS:
        try:
            response = requests.get(feed_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for event in data.get("events", []):
                    scanner_events.append({
                        "source": "scanner",
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": event
                    })
            else:
                log_event(f"[SCANNER] Failed to fetch {feed_url} - Status code: {response.status_code}")
        except Exception as e:
            log_event(f"[SCANNER] Error fetching {feed_url}: {e}")

    return scanner_events
