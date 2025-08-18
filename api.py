from fastapi import FastAPI
from typing import List, Dict, Any

app = FastAPI(title="Echo Oculus API")

# In-memory buffers (stub)
LATEST_ALERTS: List[Dict[str, Any]] = []
HEALTH: Dict[str, Any] = {}

@app.get("/alerts")
def alerts() -> List[Dict[str, Any]]:
    return LATEST_ALERTS[-100:]

@app.get("/health")
def health() -> Dict[str, Any]:
    return HEALTH
