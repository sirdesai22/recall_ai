### **AI That Watches Your Screen and Becomes Your Second Brain**

A always-on desktop agent that passively observes everything you do — every app, every document, every conversation — builds a semantic memory of your entire digital life, and lets you query it instantly in natural language.

---

#### What it does

It runs silently in the background. Then:

> _"What was that article I was reading Tuesday about distributed systems?"_ _"Find every time I've discussed pricing with a client this month"_ _"What did that contract say about payment terms?"_ _"Summarize everything I did on the Razr project last week"_

It answers instantly. With context. With the exact moment you can go back to.

---

#### This exists — Rewind.ai charges $20/month for it. You build the open source version that runs 100% locally, zero data leaving the machine.

That's the positioning. Privacy-first, free, open source.

---

#### How it works technically

**Capture layer**

- Screenshots every 5 seconds, only when screen content changes (perceptual hash diff — don't capture if nothing changed)
- OCR every screenshot with Tesseract — extracts all visible text
- Audio capture optional — transcribes with Whisper locally
- App + window title logged with every frame

**Processing pipeline**

- Deduplicate near-identical frames
- Chunk extracted text into semantic units
- Embed with a local embedding model (nomic-embed or similar, runs on CPU)
- Store in a local vector database (LanceDB — pure Python, no server needed)
- Keep a raw timeline in SQLite — every moment, every app, searchable by time

**Query layer**

- Natural language query → embed → vector search → retrieve relevant moments
- Claude gets: your query + retrieved context + timestamps
- Returns a precise answer with "you saw this at 3:42pm on Tuesday in Chrome"

**Privacy layer**

- Sensitive app detection — pause capture when 1Password, banking apps, or incognito windows are active
- All processing local — embeddings, OCR, everything
- Encrypted SQLite database
- One-click purge for any time range

---

#### Hard technical parts

|Problem|Why it's non-trivial|
|---|---|
|Perceptual hashing|Detect meaningful screen changes without capturing every frame — dHash or pHash on downsampled screenshots|
|OCR at scale|Tesseract on every frame gets slow — you build a queue with priority, skip frames under load|
|Chunking screen content|Raw OCR text is messy — you build a cleaner that reconstructs coherent text from scattered screen elements|
|Temporal reasoning|"Last Tuesday" means your query layer understands time ranges and filters the vector search accordingly|
|Memory compression|After 30 days raw frames get summarized and compressed — you can't keep everything forever|
|Sensitive content detection|Detecting banking/password apps by window title + process name before capturing|

---

#### Stack

- **Python** — entire pipeline, this is your Python mastery project
- **Tesseract** — OCR
- **Whisper** — local audio transcription
- **LanceDB** — local vector database, pure Python, no server
- **SQLite** — raw timeline storage
- **Claude API** — query answering
- **Electron or Tauri** — system tray app, always running
- **React** — search UI

---

#### Why it's technically impressive

This isn't calling an API and showing results. You're building:

- A real-time screen processing pipeline with intelligent frame dropping
- A local embedding + vector search system with no cloud dependency
- Temporal + semantic hybrid retrieval
- A privacy-preserving architecture that processes sensitive data entirely on-device

The combination of computer vision (OCR, perceptual hashing), local ML (embeddings, Whisper), and semantic search is a rare skillset. Most developers have touched one of these — you'll have built a production system combining all three.

---

#### The demo

You open your laptop in an interview, run a query about something you were doing last week, and it pulls up the exact moment with context. Nobody in that room has seen anything like it built by a single developer.

---

#### Resume story

_"Built a privacy-first AI memory system that continuously captures screen activity, runs local OCR and embeddings, and enables natural language search across your entire digital history — zero cloud dependency, fully encrypted."_

**Timeline: 4–5 weeks** for something genuinely impressive.