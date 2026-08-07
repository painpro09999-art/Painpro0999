"""
transcribe.py — wraps a whisper.cpp binary to transcribe a WAV chunk
to plain text.

Requires whisper.cpp to be built with a model downloaded. See README.md
for setup instructions.
"""

import subprocess


def transcribe_chunk(wav_path: str, binary_path: str, model: str) -> str:
    """
    Runs whisper.cpp on the given WAV file and returns the transcribed
    text as a single string. Returns an empty string on failure rather
    than raising, since a single bad chunk shouldn't kill the loop.
    """
    cmd = [
        binary_path,
        "-m", f"models/ggml-{model}.bin",
        "-f", wav_path,
        "-nt",           # no timestamps in output
        "-otxt",         # write plain text alongside stdout
        "--no-prints",   # suppress progress/debug noise
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[transcribe] whisper.cpp error: {result.stderr.strip()}")
        return ""

    return result.stdout.strip()
