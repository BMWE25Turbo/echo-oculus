# modules/audio_transcriber.py

import os
import tempfile
import ffmpeg
from pydub import AudioSegment
import whisper
from datetime import datetime
from modules.constants import SCANNER_AUDIO_STREAMS, SCANNER_KEYWORDS
from modules.utils import log_event

model = whisper.load_model("base")  # Use "tiny" for fastest, "base" is a good middle ground

def transcribe_scanner_audio():
    found_events = []

    for stream_url in SCANNER_AUDIO_STREAMS:
        try:
            # Download a 30-second audio chunk
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                (
                    ffmpeg
                    .input(stream_url, t=30)
                    .output(tmp_path, format='mp3', acodec='libmp3lame')
                    .overwrite_output()
                    .run(quiet=True)
                )

            audio = AudioSegment.from_mp3(tmp_path)
            audio.export(tmp_path.replace(".mp3", ".wav"), format="wav")

            result = model.transcribe(tmp_path.replace(".mp3", ".wav"))
            transcript = result.get("text", "").lower()

            os.remove(tmp_path)
            os.remove(tmp_path.replace(".mp3", ".wav"))

            for keyword in SCANNER_KEYWORDS:
                if keyword.lower() in transcript:
                    found_events.append({
                        "source": "scanner-audio",
                        "timestamp": datetime.utcnow().isoformat(),
                        "match": keyword,
                        "transcript": transcript.strip(),
                        "stream": stream_url
                    })

            if not found_events:
                log_event("Scanner audio processed with no keyword matches", {"url": stream_url})

        except Exception as e:
            log_event("Audio transcription error", {"error": str(e), "url": stream_url})

    return found_events
