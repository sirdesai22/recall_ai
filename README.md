# Recall

**An always-on desktop agent that builds a semantic memory of your digital life.**

Runs silently in the background, passively capturing your screen activity. Later, ask anything in natural language and get an instant answer with timestamped context.

> *"What was that article I was reading Tuesday about distributed systems?"*  
> *"Find every time I discussed pricing with a client this month."*  
> *"Summarise everything I did on the Razr project last week."*

Answers come back like: *"At 3:42pm on Tuesday in Chrome, you were reading a GitHub PR about rate limiting in a Go service."*

No cloud, no subscriptions, no data leaving your machine.

---

## Demo

![demo](https://img.shields.io/badge/status-building-yellow)

## Features

- **Continuous capture** — screenshots every 5s with perceptual hash dedup (dHash). Only stores frames where the screen actually changed.
- **Local OCR** — Tesseract extracts text from every frame. Cleaned and deduplicated.
- **Semantic chunking** — cleaned text is split into overlapping 150-word chunks for precise retrieval.
- **Vector search** — nomic-embed-text via Ollama, stored in LanceDB. Natural language queries find semantically relevant moments.
- **Temporal queries** — *"what was I reading last Tuesday"* automatically filters by time range before searching.
- **LLM answers** — retrieved chunks are passed to Llama 3, which generates a concise answer with timestamps and app names.
- **Memory compression** — nightly job groups old frames (>30 days) into app sessions, summarises each with Llama 3, and deletes the raw data. Old history stays queryable at a coarser granularity.
- **Privacy-first** — pause button, date-range purge, all processing stays local. Zero data sent to any cloud.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Electron (app/)                  │
│  ┌─────────────┐  ┌──────────────────────────┐   │
│  │  main.js    │  │  React UI (Vite + React)  │   │
│  │  (spawns    │  │  - search bar             │   │
│  │   Python)   │  │  - results + answer       │   │
│  │  (system    │  │  - pause/resume           │   │
│  │   tray)     │  │  - filter / purge         │   │
│  └──────┬──────┘  └──────────────────────────┘   │
└─────────┼───────────────────────────────────────┘
          │ spawns
┌─────────▼───────────────────────────────────────┐
│              Python Backend (core/)               │
│                                                   │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ capture.py  │  │ api.py   │  │ compress.py  │  │
│  │ - mss       │  │ FastAPI  │  │ compression  │  │
│  │ - dHash     │  │ :8765    │  │ + purge      │  │
│  │ - OCR       │  └────┬─────┘  └─────────────┘  │
│  └──────┬──────┘       │                          │
│         │              │                          │
│  ┌──────▼──────────────▼──────────────────────┐  │
│  │              Storage                        │  │
│  │  ┌──────────┐  ┌────────────────────────┐   │  │
│  │  │ SQLite   │  │  LanceDB               │   │  │
│  │  │ frames   │  │  - chunks (vectors)    │   │  │
│  │  │summaries │  │  - summaries (vectors) │   │  │
│  │  └──────────┘  └────────────────────────┘   │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐    │
│  │ Ollama     │  │Tesseract │  │ temporal  │    │
│  │ nomic-embed│  │  OCR     │  │ .py       │    │
│  │ llama3     │  │          │  │ time parse│    │
│  └────────────┘  └──────────┘  └───────────┘    │
└───────────────────────────────────────────────────┘
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Capture | Python, mss, imagehash (dHash), pytesseract |
| OCR | Tesseract |
| Embeddings | Ollama + nomic-embed-text |
| Vector DB | LanceDB (embedded, no server) |
| Timeline | SQLite |
| LLM | Llama 3 (via Ollama) |
| Backend API | FastAPI, uvicorn |
| Desktop | Electron |
| Frontend | React (Vite) |
| Fonts | Inter, JetBrains Mono |

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+
- [Ollama](https://ollama.com) with models pulled:
  ```sh
  ollama pull nomic-embed-text
  ollama pull llama3
  ```
- [Tesseract](https://github.com/tesseract-ocr/tesseract) (OCR engine)
  ```sh
  brew install tesseract     # macOS
  sudo apt install tesseract # Linux
  ```

### Setup

```sh
# Clone
git clone https://github.com/your-username/recall.git && cd recall

# Python backend
python3 -m venv core/.venv
source core/.venv/bin/activate
pip install -r core/requirements.txt

# Electron frontend
cd app && npm install && cd ..
```

### Run

**Terminal 1 — Vite dev server:**
```sh
cd app && npx vite
```

**Terminal 2 — Electron (auto-starts Python + capture loop):**
```sh
cd app && npx electron .
```

---

## Usage

- **Search** — type a query and press Enter. Results show as an LLM-generated answer + source chunks with timestamps.
- **Temporal queries** — try *"what was I reading yesterday"*, *"show me code from last Tuesday"*, *"what happened this morning"*.
- **Pause/Resume** — click the Pause button in the header to stop capture.
- **Filter** — use the Filter button in the footer for date-range pre-filtering.
- **Purge** — use Purge range to permanently delete data within a date range.

---

## Project Structure

```
recall/
├── core/                    # Python backend
│   ├── capture.py           # Capture engine (screenshot → OCR → embed → store)
│   ├── api.py               # FastAPI server (search, pause, purge)
│   ├── query.py             # Vector search + Llama 3 answer generation
│   ├── compress.py          # Memory compression (session grouping + summarisation)
│   ├── temporal.py          # Time expression parser (today, yesterday, last Tuesday, etc.)
│   ├── ocr.py               # Text cleaning + chunking
│   ├── frames/              # Saved screenshots
│   ├── frames.db            # SQLite timeline
│   └── lancedb/             # Vector database
├── app/                     # Electron frontend
│   ├── main.js              # Electron main process
│   ├── index.html           # Entry point with design tokens
│   ├── src/
│   │   ├── App.jsx          # React UI
│   │   └── main.jsx         # React mount
│   ├── package.json
│   └── vite.config.js
├── ABOUT.md
├── PLAN.md
└── README.md
```

---

## License

MIT
