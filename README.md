radio-sweepstakes-detector/
├── README.md
├── requirements.txt
├── config.yaml          # station list + stream URLs + keywords
├── capture.py           # ffmpeg stream → audio chunks
├── transcribe.py        # whisper.cpp wrapper
├── detect.py            # keyword matching on transcripts
├── main.py               # orchestrates the loop
└── logs/                 # gitignored — hit logs go here
personal-use listening/logging tool — not an auto-entry bot
