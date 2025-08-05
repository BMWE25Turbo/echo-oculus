import requests
import json
from .utils import log_event
from .constants import WAZE_FEED_URL

def fetch_waze_alerts():
    try:
        response = requests.get(WAZE_FEED_URL)
        if response.status_code != 200:
            log_event("Waze fetch failed", {"status": response.status_code})
            return []

        alerts = response.json().get("alerts", [])
        police_alerts = [alert for alert in alerts if alert.get("type") == "POLICE"]
        log_event("Fetched Waze police alerts", {"count": len(police_alerts)})
        return police_alerts

    except Exception as e:
        log_event("Exception during Waze fetch", {"error": str(e)})
        return []
