# Radio Sweepstakes Detector

A small tool that listens to live radio streams, transcribes them locally
with [whisper.cpp](https://github.com/ggerganov/whisper.cpp), and flags
segments that mention sweepstakes, giveaways, or contests — so you never
miss a call-in or text-to-win window.

**What this is:** a personal listening/logging aid. It transcribes audio
and writes matches to a log file for you to review and act on yourself.

**What this is not:** an auto-entry bot. It does not call, text, or submit
entries on your behalf. Most station contest rules require a human to
actually enter, and many prohibit automated entries — this tool only
helps you *notice* an opportunity faster.

---

## How it works

```
[ live stream ] -> ffmpeg -> [ audio chunks ] -> whisper.cpp -> [ transcript ]
                                                                      |
                                                                      v
                                                keyword/regex match -> log
```

Each configured station runs in its own thread, continuously capturing
short audio chunks, transcribing them, and checking the transcript
against a configurable keyword/regex list.

---

## Setup

### 1. Install dependencies

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
pip install -r requirements.txt
```

### 2. Build whisper.cpp and download a model

```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
bash ./models/download-ggml-model.sh base.en
```

Copy or symlink the resulting `models/ggml-base.en.bin` into this
project's `models/` directory, and note the path to the built
`whisper-cli` (or `main`) binary — you'll need both for `config.yaml`.

### 3. Get a direct stream URL for each station

Most station "Listen Live" buttons open a JavaScript player, not a
direct audio file — you need the actual stream URL underneath it.

1. Open the station's listen-live page in a **desktop** browser
   (Chrome or Firefox — dev tools are easiest here).
2. Open DevTools (`F12`) → **Network tab** → filter by "Media".
3. Click play on the station's player.
4. Look for a request ending in `.mp3`, `.aac`, or `.m3u8` — that URL
   is what goes in `config.yaml`.

Common streaming backends you'll run into (each has the same basic
extraction process above): AmperWave, SecureNet Systems, StreamTheWorld,
iHeartRadio, TuneIn.

### 4. Configure stations and keywords

Edit `config.yaml` — replace each `REPLACE_WITH_DIRECT_STREAM_URL` with
the URL you found above, and adjust the keyword/regex lists to taste.

### 5. Run it

```bash
python main.py
```

**Verifying it works end-to-end:** `config.yaml` ships with a test
station (WCPE, a classical station with an officially published direct
stream URL) and a temporary `"music"` keyword. Since WCPE talks about
music constantly, you should see hits appear in `logs/hits.jsonl`
within a minute or two of starting the script — that confirms capture,
transcription, and detection are all wired up correctly. Once
confirmed, remove the WCPE entry and the `"music"` test keyword from
`config.yaml` and fill in your real station URLs.

Hits are appended to `logs/hits.jsonl`, one JSON object per line:

```json
{"timestamp": "2026-08-06T15:04:00+00:00", "station": "WFEA 1370 AM", "hits": ["text to win"], "transcript": "...text WIN to 55555 for your chance..."}
```

---

## Running in GitHub Codespaces

This project runs fine in a Codespace — `ffmpeg` and Python are
available in the default container. A couple of Codespaces-specific
notes:

- Building whisper.cpp takes a few minutes on first setup; it's a
  one-time cost per Codespace unless you rebuild the container.
- Codespaces has a network egress limit on free tiers — continuous
  24/7 streaming may hit that if you leave it running for a long time.
  Check your plan's limits if you plan to run this unattended.
- Since Codespaces containers stop when idle, this isn't well-suited
  to true 24/7 monitoring unless you're on a plan/config that keeps it
  alive — it's better for development and testing here, with longer
  unattended runs happening on a machine you control (e.g. your phone
  setup or a dedicated rig later).

---

## Notes on accuracy

- Smaller Whisper models (`tiny`, `base`) are faster but less accurate;
  bump to `small` if you have the CPU headroom and want fewer missed or
  garbled transcriptions.
- Keyword matching is intentionally simple (substring + regex) rather
  than ML-based — it's fast, transparent, and easy to tune by hand.
  Expect some false positives (e.g. song lyrics); review the log rather
  than trusting it blindly.

## License

MIT — see LICENSE.
