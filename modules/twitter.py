import requests
from .utils import log_event
from .constants import TWITTER_KEYWORDS, TWITTER_FEEDS

def fetch_twitter_alerts():
    alerts = []

    for feed_url in TWITTER_FEEDS:
        try:
            response = requests.get(feed_url, headers={"User-Agent": "EchoOculusBot/1.0"})
            if response.status_code != 200:
                log_event("Twitter fetch failed", {"url": feed_url, "status": response.status_code})
                continue

            data = response.json()
            tweets = data.get("tweets", [])

            for tweet in tweets:
                text = tweet.get("text", "").lower()
                if any(keyword in text for keyword in TWITTER_KEYWORDS):
                    alerts.append({
                        "text": tweet.get("text"),
                        "author": tweet.get("author", {}).get("name"),
                        "timestamp": tweet.get("timestamp"),
                        "link": tweet.get("link")
                    })

            log_event("Fetched Twitter alerts", {"feed": feed_url, "count": len(alerts)})

        except Exception as e:
            log_event("Exception during Twitter fetch", {"error": str(e)})

    return alerts
