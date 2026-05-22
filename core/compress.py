import sqlite3, datetime, lancedb, ollama

DB_PATH = "frames.db"
LANCEDB_PATH = "lancedb"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"
SESSION_GAP = 300
MIN_FRAMES = 3
SUMMARY_WORD_CAP = 3000
TAIL_WORDS = 1000


def group_into_sessions(rows):
    if not rows:
        return []
    sessions = []
    current = [rows[0]]
    for row in rows[1:]:
        gap = row["timestamp"] - current[-1]["timestamp"]
        if gap > SESSION_GAP or row["app_name"] != current[-1]["app_name"]:
            sessions.append(current)
            current = [row]
        else:
            current.append(row)
    sessions.append(current)
    return [s for s in sessions if len(s) >= MIN_FRAMES]


def summarise_session(session):
    words = []
    for row in session:
        words.extend(row["raw_text"].split())
    if len(words) > SUMMARY_WORD_CAP:
        words = words[:TAIL_WORDS] + words[-(TAIL_WORDS):]
    text = " ".join(words)

    prompt = (
        "Summarise what the user was doing in 2-3 factual sentences. "
        "Include the app, the content/task, and specifics. "
        'Not "browsing the web" — "reading a GitHub PR about rate limiting in Go".\n\n'
        f"App: {session[0]['app_name']}\n"
        f"Screen content:\n{text}"
    )

    resp = ollama.chat(model=LLM_MODEL, messages=[
        {"role": "user", "content": prompt},
    ])
    return resp["message"]["content"].strip()


def embed_text(text):
    resp = ollama.embed(model=EMBED_MODEL, input=text)
    return resp["embeddings"][0]


def ensure_summaries_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_timestamp REAL NOT NULL,
            end_timestamp REAL NOT NULL,
            app_name TEXT,
            summary_text TEXT,
            frame_count INTEGER
        )
    """)
    conn.commit()


def ensure_summaries_lancedb(db):
    try:
        tbl = db.open_table("summaries")
    except Exception:
        tbl = db.create_table("summaries", [
            {"vector": [0.0] * 768, "chunk_text": "", "frame_id": 0,
             "timestamp": 0.0, "app_name": "", "window_title": "",
             "is_summary": True}
        ], mode="overwrite")
        tbl.delete("frame_id >= 0")


def run_compression():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_summaries_table(conn)

    vec_db = lancedb.connect(LANCEDB_PATH)
    ensure_summaries_lancedb(vec_db)
    vec_tbl = vec_db.open_table("summaries")
    chunks_tbl = vec_db.open_table("chunks")

    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    rows = conn.execute(
        "SELECT * FROM frames WHERE timestamp < ? ORDER BY timestamp",
        (cutoff.timestamp(),),
    ).fetchall()

    if not rows:
        print(f"[compress] no frames older than 30 days", flush=True)
        return

    sessions = group_into_sessions([dict(r) for r in rows])
    print(f"[compress] {len(sessions)} sessions in {len(rows)} old frames", flush=True)

    for session in sessions:
        summary = summarise_session(session)
        start_ts = session[0]["timestamp"]
        end_ts = session[-1]["timestamp"]
        app_name = session[0]["app_name"]
        frame_ids = [r["id"] for r in session]

        cur = conn.execute(
            "INSERT INTO summaries (start_timestamp, end_timestamp, app_name, summary_text, frame_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (start_ts, end_ts, app_name, summary, len(session)),
        )
        summary_id = cur.lastrowid

        embedding = embed_text(summary)
        vec_tbl.add([{
            "vector": embedding,
            "chunk_text": summary,
            "frame_id": None,
            "timestamp": start_ts,
            "app_name": app_name,
            "window_title": "",
            "is_summary": True,
        }])

        placeholders = ",".join("?" for _ in frame_ids)
        conn.execute(f"DELETE FROM frames WHERE id IN ({placeholders})", frame_ids)
        chunks_tbl.delete(f"frame_id IN ({','.join(str(f) for f in frame_ids)})")
        conn.commit()

        print(f"[compress] summarised session: {app_name} ({len(session)} frames) → summary_id={summary_id}", flush=True)

    conn.close()
    print(f"[compress] done — {len(sessions)} sessions compressed", flush=True)


def purge_range(start_ts, end_ts):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    vec_db = lancedb.connect(LANCEDB_PATH)
    chunks_tbl = vec_db.open_table("chunks")

    rows = conn.execute(
        "SELECT id FROM frames WHERE timestamp >= ? AND timestamp <= ?",
        (start_ts, end_ts),
    ).fetchall()
    frame_ids = [r["id"] for r in rows]

    if not frame_ids:
        print(f"[purge] no frames in range", flush=True)
        conn.close()
        return

    placeholders = ",".join("?" for _ in frame_ids)
    conn.execute(f"DELETE FROM frames WHERE id IN ({placeholders})", frame_ids)
    chunks_tbl.delete(f"frame_id IN ({','.join(str(f) for f in frame_ids)})")
    conn.commit()
    conn.close()
    print(f"[purge] deleted {len(frame_ids)} frames", flush=True)
