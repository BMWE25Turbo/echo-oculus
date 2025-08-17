# modules/audio_transcriber.py
import os, tempfile, threading, time
from datetime import datetime, timezone
import ffmpeg
from pydub import AudioSegment
import whisper

from modules.constants import SCANNER_AUDIO_STREAMS, SCANNER_KEYWORDS
from modules.utils import log_event

def _utc_now_iso():
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")

# Lazy model loader (env or config can override)
_MODEL_NAME_ENV = os.environ.get("EO_WHISPER_MODEL")
_model = None
def _get_model(name: str | None):
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

def _score_keywords(transcript_lower: str):
    hits = []
    for kw in SCANNER_KEYWORDS:
        k = kw.lower()
        if k in transcript_lower:
            count = transcript_lower.count(k)
            conf = round(0.60 + min(0.30, 0.05 * (count - 1)), 2)
            hits.append((kw, conf))
    return hits

def _cleanup(paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

def transcribe_scanner_audio(max_seconds: int = 20, streams: list[str] | None = None, model_name: str | None = None):
    """Manual utility: process once; return hit events (transient)."""
    streams = streams or SCANNER_AUDIO_STREAMS or []
    events = []
    for url in streams:
        mp3 = wav = None
        try:
            # grab short chunk
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as t:
                mp3 = t.name
            (
                ffmpeg
                .input(url, t=max_seconds)
                .output(mp3, format="mp3", acodec="libmp3lame", ar="16000", ac=1)
                .overwrite_output()
                .global_args("-loglevel", "error")
                .run(quiet=True)
            )
            # normalize to wav 16k mono
            audio = AudioSegment.from_file(mp3, format="mp3").set_frame_rate(16000).set_channels(1)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as w:
                wav = w.name
            audio.export(wav, format="wav")

            # ASR
            model = _get_model(model_name)
            res = model.transcribe(wav, fp16=False)
            text = (res.get("text") or "").strip()
            lower = text.lower()

            # keywords
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
            log_event("Scanner audio processed",
                      {"url": url, "matches": [{"kw": m, "conf": c} for m, c in matches]})
        except Exception as e:
            log_event("Audio transcription error", {"url": url, "error": str(e)}, level="ERROR")
        finally:
            _cleanup([mp3, wav])
    return events

class ScannerAudioWorker(threading.Thread):
    """Background worker: periodic transient scanning; emits hits via callback(event)."""
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

    def stop(self): self._running = False

    def run(self):
        if not self.enabled:
            log_event("ScannerAudioWorker disabled; not starting")
            return
        if self.legal.get("tos_compliant_only", True) and not self.streams:
            log_event("ScannerAudioWorker has no compliant streams; exiting")
            return
        if not self.legal.get("transient_only", True):
            log_event("ScannerAudioWorker requires transient_only=true; exiting for safety", level="WARNING")
            return

        self._running = True
        log_event("ScannerAudioWorker started", {
            "interval_s": self.interval, "chunk_s": self.chunk, "streams": len(self.streams)
        })
        backoff = 1
        while self._running:
            start = time.time()
            try:
                events = transcribe_scanner_audio(self.chunk, self.streams, self.model)
                # emit hits immediately (RAM only; caller decides persistence)
                for ev in events:
                    try:
                        self.on_event(ev)
                    except Exception as e:
                        log_event("ScannerAudioWorker on_event failed", {"error": str(e)}, level="WARNING")
                backoff = 1  # reset on success
            except Exception as e:
                log_event("ScannerAudioWorker iteration error", {"error": str(e)}, level="WARNING")
                backoff = min(60, backoff * 2)
            # sleep remaining interval (+ backoff if error)
            elapsed = time.time() - start
            sleep_for = max(1, self.interval - int(elapsed)) + (0 if backoff == 1 else backoff)
            time.sleep(sleep_for)
        log_event("ScannerAudioWorker stopped")

