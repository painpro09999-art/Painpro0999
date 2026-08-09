"""
extract.py — takes a flagged transcript chunk and asks a local SLM
(via Ollama) to pull out structured sweepstakes/contest fields.

This runs only when detect.py has already found a keyword/regex hit,
so it's an occasional call, not a continuous load — it doesn't compete
with Whisper for resources the way running both continuously would.

Requires Ollama running locally with the configured model pulled, e.g:
    ollama pull qwen2.5:1.5b
"""

import json
import urllib.request
import urllib.error


EXTRACTION_PROMPT = """You are extracting structured information from a \
radio transcript snippet that mentions a contest, sweepstakes, or giveaway.

Read the transcript below and respond with ONLY a JSON object (no other \
text, no markdown formatting) with these fields. Use null for any field \
not mentioned in the transcript:

{{
  "sponsor": "station or company name, or null",
  "prize": "description of the prize, or null",
  "prize_amount": "dollar amount if mentioned, or null",
  "entry_method": "how to enter — call, text, online, or null",
  "contact_info": "phone number, shortcode, or URL mentioned, or null",
  "deadline": "any deadline mentioned, or null"
}}

Transcript:
\"\"\"{transcript}\"\"\"

JSON:"""


def extract_fields(transcript: str, cfg: dict) -> dict:
    """
    Calls a local Ollama model to extract structured fields from a
    transcript. Returns a dict of fields, or a dict with an "error"
    key if the call fails or the response isn't valid JSON — callers
    should still log the raw transcript in that case rather than
    dropping the hit.
    """
    prompt = EXTRACTION_PROMPT.format(transcript=transcript)

    payload = json.dumps({
        "model": cfg["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},  # low temp — this is extraction, not creative writing
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{cfg['ollama_host']}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 60)) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as e:
        return {"error": f"ollama request failed: {e}"}

    raw_output = body.get("response", "").strip()

    # Models sometimes wrap JSON in markdown fences despite instructions
    # not to — strip those before parsing.
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`")
        if raw_output.lower().startswith("json"):
            raw_output = raw_output[4:].strip()

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return {"error": "model did not return valid JSON", "raw_output": raw_output}
