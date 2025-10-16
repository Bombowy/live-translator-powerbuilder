# Live Translator (PowerBuilder + FastAPI + Oracle)

🚀 Real-time AI translator combining:
- **PowerBuilder 2025** (desktop + PowerServer web)
- **Oracle XE 21c** (as main database)
- **FastAPI** backend for ASR/MT/TTS
- **Python Edge Agent** (low-latency audio stream)
- Zero-shot or fine-tuned TTS in user's voice

## 🧩 Structure
- `pb-client/` — PowerBuilder UI and REST client
- `backend/` — FastAPI backend
- `oracle/` — Database schema and initialization
- `edge-agent/` — Local Python audio capture and streamer

## 💻 Setup
1. Install Oracle XE + Instant Client (32-bit for PowerBuilder)
2. Run schema:
   ```sql
   @oracle/01_schema.sql
