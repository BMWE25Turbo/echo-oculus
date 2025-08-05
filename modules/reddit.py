import requests
from .utils import log_event
from .constants import REDDIT_KEYWORDS, REDDIT_FEEDS

def fetch_reddit_alerts():
    alerts = []

    for feed_url in REDDIT_FEEDS:
        try:
            response = requests.get(feed_url, headers={"User-Agent": "EchoOculusBot/1.0"})
            if response.status_code != 200:
                log_event("Reddit fetch failed", {"url": feed_url, "status": response.status_code})
                continue

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                title = post["data"].get("title", "").lower()
                if any(keyword in title for keyword in REDDIT_KEYWORDS):
                    alerts.append({
                        "title": post["data"].get("title"),
                        "url": post["data"].get("url"),
                        "subreddit": post["data"].get("subreddit"),
                        "timestamp": post["data"].get("created_utc")
                    })

            log_event("Fetched Reddit alerts", {"feed": feed_url, "count": len(alerts)})

        except Exception as e:
            log_event("Exception during Reddit fetch", {"error": str(e)})

    return alerts
