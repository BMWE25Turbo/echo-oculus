# --- Existing constants (kept for backward compatibility) ---
WAZE_API_URL = "https://www.waze.com/row-rtserver/web/TGeoRSS"
TWITTER_QUERY_TAGS = ["police", "cop", "speed trap"]
REDDIT_SUBS = ["r/Portland", "r/OregonCity", "r/Oregon"]
ALERT_RADIUS_MILES = 1.5
SCANNER_AUDIO_STREAMS = [
    "https://example-broadcastify-feed.com/live.mp3"
]
SCANNER_KEYWORDS = [
    "pursuit", "officer", "suspect", "traffic stop", "armed", "shots fired",
    "backup", "fleeing", "high speed", "taser", "code 3", "car accident"
]

# --- Phase 1 weighting & thresholds (safe defaults; can be overridden in config) ---
DEFAULT_SOURCE_WEIGHTS = {
    "scanner": 0.9,
    "waze": 0.7,
    "reddit": 0.55,
    "news": 0.6,
}
SEVERITY_THRESHOLDS = {
    # Used by AlertEngine: combine with distance buckets
    "min_confidence": 0.60,
    "med_confidence": 0.65,
    "high_confidence": 0.75,
}

# --- Phase 1.5 retention & cooldown defaults (mirrors config but ok to use in code) ---
DEFAULT_COOLDOWN_MIN = 30       # police alert cooldown
DEFAULT_ALERT_RADIUS_MI = 2.5   # if config missing, use this

# --- Legal guardrails (non-negotiable; referenced by vision/audio modules later) ---
LEGAL_GUARDS = {
    "no_faces": True,
    "no_plates": True,
    "tos_compliant_only": True,
    "transient_audio_only": True,  # transcribe → score → discard
}

# --- Phase 2/2.5 scaffolding ---
WEATHER_PROVIDERS = ["open-meteo", "nws"]
DEFAULT_UNITS = "imperial"
STORAGE_DEFAULTS = {
    "data_dir": "/data",
    "hot_days": 30,
    "warm_months": 24,
    "max_years": 3,
}

# --- Phase 3: WOT-RES (route scoring) scaffold ---
WOT_RES_DEFAULT_WEIGHTS = {
    "cop_activity": 0.50,
    "road_quality": 0.30,
    "traffic_flow": 0.20,
}

# --- Phase 5: ML/Heat-zone interface placeholders ---
ML_DEFAULTS = {
    "heatmap_enabled": True,
    "model_dir": "/models",
    "quantized": True,
}
