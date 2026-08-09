"""
main.py — orchestrates the radio sweepstakes detector.

For each configured station, runs a loop: capture a short audio chunk
from the live stream -> transcribe it -> check for sweepstakes-related
keywords/patterns -> log any hits. Runs one station per thread so
multiple stations can be monitored concurrently.

Usage:
    python main.py [--config config.yaml]
"""

import argparse
import json
import os
import threading
import time
from datetime import datetime, timezone

import yaml

from capture import capture_loop
from transcribe import transcribe_chunk
from detect import find_hits
from extract import extract_fields


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def log_hit(log_path: str, station: str, hits: list, transcript: str, extracted: dict = None):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station": station,
        "hits": hits,
        "transcript": transcript,
        "extracted": extracted,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    summary = extracted.get("prize") if extracted and "error" not in extracted else None
    print(f"[HIT] {station} — {hits} — {summary or transcript[:120]}")


def monitor_station(station_cfg: dict, cfg: dict):
    name = station_cfg["name"]
    stream_url = station_cfg["stream_url"]
    chunk_seconds = station_cfg.get("chunk_seconds", 15)

    tmp_dir = os.path.join(cfg["audio_tmp_dir"], name.replace(" ", "_"))
    log_path = cfg["log_path"]
    whisper_binary = cfg["whisper"]["binary_path"]
    whisper_model = cfg["whisper"]["model"]
    keywords = cfg.get("keywords", [])
    regex_patterns = cfg.get("regex_patterns", [])

    print(f"[main] starting monitor for {name}")

    for chunk_path in capture_loop(stream_url, chunk_seconds, tmp_dir):
        transcript = transcribe_chunk(chunk_path, whisper_binary, whisper_model)

        # Chunk audio file is no longer needed once transcribed.
        try:
            os.remove(chunk_path)
        except OSError:
            pass

        if not transcript:
            continue

        hits = find_hits(transcript, keywords, regex_patterns)
        if hits:
            extracted = None
            if cfg.get("extraction", {}).get("enabled"):
                extracted = extract_fields(transcript, cfg["extraction"])
            log_hit(log_path, name, hits, transcript, extracted)


def main():
    parser = argparse.ArgumentParser(description="Radio sweepstakes detector")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    stations = cfg.get("stations", [])

    if not stations:
        print("No stations configured in config.yaml — nothing to do.")
        return

    placeholder_stations = [
        s["name"] for s in stations
        if "REPLACE_WITH" in s.get("stream_url", "")
    ]
    if placeholder_stations:
        print(
            "The following stations still have placeholder stream URLs "
            f"in config.yaml and will be skipped: {placeholder_stations}"
        )

    threads = []
    for station_cfg in stations:
        if "REPLACE_WITH" in station_cfg.get("stream_url", ""):
            continue
        t = threading.Thread(target=monitor_station, args=(station_cfg, cfg), daemon=True)
        t.start()
        threads.append(t)

    if not threads:
        print("No stations with a valid stream_url — update config.yaml and rerun.")
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[main] shutting down.")


if __name__ == "__main__":
    main()
