"""
Echo Oculus constants
- Backwards-compatible with your original constants.
- Adds structured defaults used by the new modules.
- Central place for legal guardrails and future-phase scaffolding.
"""

# ----------------------------
# Original constants you had
# ----------------------------
WAZE_API_URL = "https://www.waze.com/row-rtserver/web/TGeoRSS"

TWITTER_QUERY_TAGS = ["police", "cop", "speed trap"]

REDDIT_SUBS = ["r/Portland", "r/OregonCity", "r/Oregon"]

# (legacy radius used by some early code)
ALERT_RADIUS_MILES = 1.5

# If you ever feed an audio URL directly, keep this here for debug/manual tests
SCANNER_AUDIO_STREAMS = [
    "https://example-broadcastify-feed.com/live.mp3"
]

SCANNER_KEYWORDS = [
    "pursuit", "officer", "suspect", "traffic stop", "armed", "shots fired",
    "backup", "fleeing", "high speed", "taser", "code 3", "car accident"
]

# Your early weighting/threshold ideas (kept for reference/back-compat)
DEFAULT_SOURCE_WEIGHTS = {
    "scanner": 0.9,
    "waze": 0.7,
    "reddit": 0.55,
    "news": 0.6,
}
SEVERITY_THRESHOLDS = {
    "min_confidence": 0.60,
    "med_confidence": 0.65,
    "high_confidence": 0.75,
}

DEFAULT_COOLDOWN_MIN = 30        # police alert cooldown (minutes)
DEFAULT_ALERT_RADIUS_MI = 2.5    # radius fallback if config missing

LEGAL_GUARDS = {
    "no_faces": True,
    "no_plates": True,
    "tos_compliant_only": True,
    "transient_audio_only": True,  # transcribe → score → discard
}

WEATHER_PROVIDERS = ["open-meteo", "nws"]
DEFAULT_UNITS = "imperial"
STORAGE_DEFAULTS = {
    "data_dir": "/data",
    "hot_days": 30,
    "warm_months": 24,
    "max_years": 3,
}

WOT_RES_DEFAULT_WEIGHTS = {
    "cop_activity": 0.50,
    "road_quality": 0.30,
    "traffic_flow": 0.20,
}

ML_DEFAULTS = {
    "heatmap_enabled": True,
    "model_dir": "/models",
    "quantized": True,
}

# ----------------------------
# Structured constants used by the new modules
# (These are what DataSources/AlertEngine expect.)
# ----------------------------

# JSON/REST scanner feeds (not audio). Override from config if you have any.
SCANNER_JSON_FEEDS: list[str] = []

# Canonical minimum confidence a report must have *after* weighting
MIN_CONFIDENCE = SEVERITY_THRESHOLDS.get("min_confidence", 0.60)

# Per-source weights used when blending confidences from feeds
SOURCE_WEIGHTS = {
    # map your legacy names to concrete sources used in code paths
    "waze"         : DEFAULT_SOURCE_WEIGHTS.get("waze", 0.7),
    "reddit"       : DEFAULT_SOURCE_WEIGHTS.get("reddit", 0.55),
    "twitter-news" : DEFAULT_SOURCE_WEIGHTS.get("news", 0.6),
    "scanner-json" : DEFAULT_SOURCE_WEIGHTS.get("scanner", 0.9),
    "scanner-audio": DEFAULT_SOURCE_WEIGHTS.get("scanner", 0.9),
}

# Cooldowns per source (seconds). Uses your DEFAULT_COOLDOWN_MIN as a base.
_DEFAULT_CD_S = int(DEFAULT_COOLDOWN_MIN * 60)
SOURCE_COOLDOWN_S = {
    "waze"         : _DEFAULT_CD_S,      # 30 min by default
    "reddit"       : _DEFAULT_CD_S + 300,  # a bit longer (posts linger)
    "twitter-news" : _DEFAULT_CD_S + 300,
    "scanner-json" : _DEFAULT_CD_S,
    "scanner-audio": _DEFAULT_CD_S,
}

# ----------------------------
# Convenience aliases (so older code won’t break)
# ----------------------------
# Some older modules referenced these names; keep them pointing at the new structures.
SOURCE_WEIGHTS_LEGACY = SOURCE_WEIGHTS
COOLDOWN_SECONDS_BY_SOURCE = SOURCE_COOLDOWN_S
