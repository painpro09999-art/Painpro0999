"""
capture.py — pulls a live audio stream and splits it into short WAV
chunks using ffmpeg, so each chunk can be handed off to Whisper.

Requires `ffmpeg` to be installed and on PATH.
"""

import os
import subprocess
import time
import uuid


def capture_chunk(stream_url: str, chunk_seconds: int, out_dir: str) -> str:
    """
    Records `chunk_seconds` of audio from `stream_url` into a new WAV
    file inside `out_dir`. Returns the path to the file that was
    written, or raises RuntimeError if ffmpeg fails.
    """
    os.makedirs(out_dir, exist_ok=True)
    chunk_path = os.path.join(out_dir, f"chunk_{uuid.uuid4().hex}.wav")

    cmd = [
        "ffmpeg",
        "-y",                       # overwrite without prompting
        "-loglevel", "error",
        "-i", stream_url,
        "-t", str(chunk_seconds),   # duration to capture
        "-ac", "1",                 # mono
        "-ar", "16000",             # 16kHz — what whisper.cpp expects
        chunk_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(chunk_path):
        raise RuntimeError(
            f"ffmpeg failed to capture from {stream_url}:\n{result.stderr}"
        )

    return chunk_path


def capture_loop(stream_url: str, chunk_seconds: int, out_dir: str):
    """
    Generator that yields chunk file paths forever, one per
    `chunk_seconds` window. Caller is responsible for deleting each
    chunk after it's been processed.
    """
    while True:
        start = time.time()
        try:
            chunk_path = capture_chunk(stream_url, chunk_seconds, out_dir)
            yield chunk_path
        except RuntimeError as e:
            print(f"[capture] error: {e}")
            time.sleep(5)  # back off before retrying a broken stream
            continue

        # If capture was somehow faster than real-time, don't hammer
        # the stream — wait out the remainder of the window.
        elapsed = time.time() - start
        if elapsed < chunk_seconds:
            time.sleep(max(0, chunk_seconds - elapsed))
