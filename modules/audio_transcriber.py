# modules/audio_transcriber.py
import os
import threading
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import ffmpeg
import numpy as np
import whisper

from modules.constants import SCANNER_AUDIO_STREAMS, SCANNER_KEYWORDS
from modules.utils import log_event


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


# ---------- Whisper model (lazy) ----------
_MODEL_NAME_ENV = os.environ.get("EO_WHISPER_MODEL")
_model: Optional[Any] = None


def _get_model(name: Optional[str]):
    """
    Lazily load a Whisper model. Default order:
    explicit name -> EO_WHISPER_MODEL env -> 'tiny'
    """
    global _model
    target = name or _MODEL_NAME_ENV or "tiny"
    if _model is None or getattr(_model, "_eo_name", None) != target:
        try:
            m = whisper.load_model(target)
            m._eo_name = target
            _model = m
            log_event("Whisper model loaded", {"model": target})
        except Exception as e:
            log_event("Whisper load failed; falling back to tiny", {"error": str(e)}, level="WARNING")
            m = whisper.load_model("tiny")
            m._eo_name = "tiny"
            _model = m
    return _model


# ---------- Helpers ----------
def _score_keywords(transcript_lower: str):
    """
    Simple keyword matcher with heuristic confidence.
    Multiple occurrences bump confidence slightly (capped).
    """
    hits = []
    for kw in SCANNER_KEYWORDS:
        k = kw.lower()
        if k in transcript_lower:
            count = transcript_lower.count(k)
            conf = round(0.60 + min(0.30, 0.05 * (count - 1)), 2)
            hits.append((kw, conf))
    return hits


def _ffmpeg_capture_pcm(url: str, seconds: int) -> np.ndarray:
    """
    Capture ~N seconds of audio from URL to memory as 16 kHz mono PCM (float32 in [-1,1]).
    No temp files are used. Returns np.ndarray shape (samples,) dtype float32.
    """
    # Ask ffmpeg to output raw 16kHz mono signed 16-bit little-endian PCM to stdout
    # Add reconnect flags to handle short dropouts gracefully.
    try:
        out, _ = (
            ffmpeg
            .input(
                url,
                t=seconds,
                **{
                    "reconnect": "1",
                    "reconnect_streamed": "1",
                    "reconnect_delay_max": "2",
                }
            )
            .output(
                "pipe:",
                format="s16le",  # raw PCM
                acodec="pcm_s16le",
                ac=1,
                ar="16000",
            )
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
    except ffmpeg.Error as e:
        # Propagate as a normal Exception with stderr context for our logger
        raise Exception(f"ffmpeg capture error: {e.stderr.decode('utf-8', errors='ignore')}")

    if not out:
        # Sometimes streams are silent or fail transiently; handle gracefully
        return np.zeros(0, dtype=np.float32)

    # Convert raw bytes to int16 -> float32 in [-1, 1]
    pcm_i16 = np.frombuffer(out, dtype=np.int16)
    if pcm_i16.size == 0:
        return np.zeros(0, dtype=np.float32)
    pcm_f32 = (pcm_i16.astype(np.float32)) / 32768.0
    return pcm_f32


# ---------- Public API ----------
def transcribe_scanner_audio(
    max_seconds: int = 20,
    streams: Optional[List[str]] = None,
    model_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Manual utility: process each stream once; return hit events (transient).
    - Fully in-memory pipeline (no files): ffmpeg -> PCM bytes -> numpy float32
    - Normalize: 16 kHz mono
    - Whisper runs on numpy audio array (fp16=False for CPU)
    - Only short transcript snippets and keyword hits are kept.
    """
    streams = streams or SCANNER_AUDIO_STREAMS or []
    events: List[Dict[str, Any]] = []

    for url in streams:
        try:
            audio = _ffmpeg_capture_pcm(url, max_seconds)
            if audio.size == 0:
                log_event("Scanner audio empty/silent", {"url": url})
                continue

            model = _get_model(model_name)
            # Whisper accepts numpy array of float32 16k mono samples
            res = model.transcribe(audio, fp16=False)
            text = (res.get("text") or "").strip()
            lower = text.lower()

            matches = _score_keywords(lower)
            ts = _utc_now_iso()

            for kw, conf in matches:
                events.append({
                    "source": "scanner-audio",
                    "timestamp": ts,
                    "match": kw,
                    "confidence": conf,
                    "transcript_snippet": text[:160],
                    "stream": url,
                })

            log_event(
                "Scanner audio processed",
                {"url": url, "matches": [{"kw": m, "conf": c} for m, c in matches]}
            )

        except Exception as e:
            log_event("Audio transcription error", {"url": url, "error": str(e)}, level="ERROR")

    return events


class ScannerAudioWorker(threading.Thread):
    """
    Background worker: periodic transient scanning; emits hits via callback(event).
    - Respects config echo_oculus.scanner_audio
    - Requires legal.transient_only == true (safety)
    - No temp files; all audio stays in RAM and is discarded immediately after use.
    """
    def __init__(self, cfg: dict, on_event):
        super().__init__(daemon=True)
        eo = (cfg.get("echo_oculus") or {})
        a = (eo.get("scanner_audio") or {})
        self.enabled = bool(a.get("enabled", False))
        self.interval = int(a.get("interval_s", 60))
        self.chunk = int(a.get("chunk_s", 20))
        self.model = a.get("model") or None
        self.streams = list(a.get("streams") or SCANNER_AUDIO_STREAMS or [])
        self.legal = a.get("legal", {})
        self._running = False
        self.on_event = on_event

    def stop(self):
        self._running = False

    def run(self):
        if not self.enabled:
            log_event("ScannerAudioWorker disabled; not starting")
            return
        if self.legal.get("tos_compliant_only", True) and not self.streams:
            log_event("ScannerAudioWorker has no compliant streams; exiting")
            return
        if not self.legal.get("transient_only", True):
            log_event(
                "ScannerAudioWorker requires transient_only=true; exiting for safety",
                level="WARNING"
            )
            return

        self._running = True
        log_event(
            "ScannerAudioWorker started",
            {"interval_s": self.interval, "chunk_s": self.chunk, "streams": len(self.streams)}
        )

        backoff = 1
        while self._running:
            start = time.time()
            try:
                events = transcribe_scanner_audio(self.chunk, self.streams, self.model)
                # Emit hits immediately (RAM only; caller decides persistence)
                for ev in events:
                    try:
                        self.on_event(ev)
                    except Exception as e:
                        log_event("ScannerAudioWorker on_event failed", {"error": str(e)}, level="WARNING")
                backoff = 1  # reset on success
            except Exception as e:
                log_event("ScannerAudioWorker iteration error", {"error": str(e)}, level="WARNING")
                backoff = min(60, backoff * 2)

            # Sleep remaining interval (+ backoff if error)
            elapsed = time.time() - start
            sleep_for = max(1, self.interval - int(elapsed)) + (0 if backoff == 1 else backoff)
            time.sleep(sleep_for)

        log_event("ScannerAudioWorker stopped")

