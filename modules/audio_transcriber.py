# modules/audio_transcriber.py

import os
import tempfile
import ffmpeg
from pydub import AudioSegment
import whisper
from datetime import datetime, timezone
from modules.constants import SCANNER_AUDIO_STREAMS, SCANNER_KEYWORDS
from modules.utils import log_event

# Choose model at runtime:
#   export EO_WHISPER_MODEL=tiny   (fastest)
#   export EO_WHISPER_MODEL=base   (default)
#   export EO_WHISPER_MODEL=small  (if you want a bit more accuracy)
_WHISPER_MODEL_NAME = os.environ.get("EO_WHISPER_MODEL", "base")
_model = None  # lazy-loaded on first call


def _lazy_model():
    global _model
    if _model is None:
        try:
            _model = whisper.load_model(_WHISPER_MODEL_NAME)
            log_event("Whisper model loaded", {"model": _WHISPER_MODEL_NAME})
        except Exception as e:
            # Fallback to tiny if the requested model isn't available
            log_event("Whisper load failed; falling back to tiny", {"error": str(e)}, level="WARNING")
            _model = whisper.load_model("tiny")
    return _model


def _utc_now_iso():
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _score_keywords(transcript_lower: str):
    """Return list of (keyword, confidence) matches with a simple score."""
    matches = []
    for kw in SCANNER_KEYWORDS:
        k = kw.lower()
        if k in transcript_lower:
            # Heuristic confidence: longer transcripts & repeated hits get a bump.
            count = transcript_lower.count(k)
            base = 0.60
            bump = min(0.30, 0.05 * (count - 1))
            conf = round(base + bump, 2)
            matches.append((kw, conf))
    return matches


def _cleanup(paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def transcribe_scanner_audio(max_seconds: int = 30):
    """
    Pull ~30s of audio from each configured scanner stream, transcribe with Whisper,
    keyword-match, and return a list of event dicts. Raw audio is always deleted.
    """
    found_events = []
    streams = SCANNER_AUDIO_STREAMS or []

    for stream_url in streams:
        tmp_mp3 = None
        tmp_wav = None
        try:
            # ---- 1) Grab a short chunk via ffmpeg (transient) ----
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_mp3 = tmp_file.name

            (
                ffmpeg
                .input(stream_url, t=max_seconds)
                .output(tmp_mp3, format="mp3", acodec="libmp3lame", ar="16000", ac=1)  # 16 kHz mono
                .overwrite_output()
                .global_args("-loglevel", "error")
                .run(quiet=True)
            )

            # ---- 2) Normalize to WAV 16k/mono for Whisper stability ----
            audio = AudioSegment.from_file(tmp_mp3, format="mp3")
            audio = audio.set_frame_rate(16000).set_channels(1)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpw:
                tmp_wav = tmpw.name
            audio.export(tmp_wav, format="wav")

            # ---- 3) Transcribe (Whisper) ----
            model = _lazy_model()
            result = model.transcribe(tmp_wav, fp16=False)  # CPU-friendly on Pi
            transcript = (result.get("text") or "").strip()
            transcript_lower = transcript.lower()

            # ---- 4) Keyword scoring → events ----
            matches = _score_keywords(transcript_lower)
            ts = _utc_now_iso()
            for (keyword, conf) in matches:
                # Keep transcript snippet (not full) to reduce log volume
                snippet = transcript[:200]
                found_events.append({
                    "source": "scanner-audio",
                    "timestamp": ts,
                    "match": keyword,
                    "confidence": conf,
                    "transcript_snippet": snippet,
                    "stream": stream_url,
                })

            if matches:
                log_event("Scanner audio keyword matches",
                          {"url": stream_url, "matches": [{"kw": m, "conf": c} for m, c in matches]})
            else:
                log_event("Scanner audio processed with no matches", {"url": stream_url})

        except Exception as e:
            log_event("Audio transcription error", {"error": str(e), "url": stream_url}, level="ERROR")

        finally:
            # Always delete raw audio (transient by policy)
            _cleanup([tmp_mp3, tmp_wav])

    return found_events
