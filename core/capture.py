import mss, time, subprocess, sqlite3, threading
from PIL import Image
import imagehash
import pytesseract
import ollama
import lancedb
from ocr import clean_text, chunk_text

DB_PATH = "frames.db"
FRAMES_DIR = "frames"
LANCEDB_PATH = "lancedb"
EMBED_MODEL = "nomic-embed-text"


def active_window():
    script = '''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        set appName to name of frontApp
        try
            set winTitle to title of first window of frontApp
        on error
            set winTitle to ""
        end try
        return appName & "|||" & winTitle
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0 and "|||" in result.stdout:
        parts = result.stdout.strip().split("|||", 1)
        return parts[0], parts[1]
    return "", ""


def embed_text(text):
    response = ollama.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            app_name TEXT,
            window_title TEXT,
            raw_text TEXT,
            frame_path TEXT
        )
    """)
    conn.commit()
    return conn


def init_vector_store():
    db = lancedb.connect(LANCEDB_PATH)
    try:
        tbl = db.open_table("chunks")
    except Exception:
        tbl = db.create_table("chunks", [
            {"vector": [0.0] * 768, "chunk_text": "", "frame_id": 0,
             "timestamp": 0.0, "app_name": "", "window_title": ""}
        ], mode="overwrite")
        tbl.delete("frame_id >= 0")
    return db, tbl


class CaptureEngine:
    def __init__(self):
        self._running = False
        self._paused = threading.Event()
        self._paused.set()
        self._thread = None

    @property
    def paused(self):
        return not self._paused.is_set()

    def start(self):
        if self._running:
            return
        self._running = True
        self._paused.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._paused.set()
        self._thread = None

    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    def _loop(self):
        conn = init_db()
        vec_db, vec_tbl = init_vector_store()
        prev_hash = None

        with mss.MSS() as sct:
            while self._running:
                self._paused.wait()

                screenshot = sct.grab(sct.monitors[0])
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                h = imagehash.dhash(img)

                if prev_hash is not None:
                    dist = h - prev_hash
                    print(f"distance: {dist}", flush=True)
                    if dist <= 8:
                        prev_hash = h
                        time.sleep(5)
                        continue
                else:
                    print("first frame", flush=True)

                ts = time.time()
                frame_path = f"{FRAMES_DIR}/frame_{ts}.png"
                img.save(frame_path)

                app_name, win_title = active_window()
                raw_text = pytesseract.image_to_string(img)
                cleaned = clean_text(raw_text)
                print(f"--- cleaned ({len(cleaned)} chars) ---\n{cleaned[:300]}\n---", flush=True)

                cur = conn.execute(
                    "INSERT INTO frames (timestamp, app_name, window_title, raw_text, frame_path) VALUES (?, ?, ?, ?, ?)",
                    (ts, app_name, win_title, raw_text, frame_path),
                )
                frame_id = cur.lastrowid
                conn.commit()

                chunks = chunk_text(cleaned)
                rows = []
                for i, chunk in enumerate(chunks):
                    embedding = embed_text(chunk)
                    rows.append({
                        "vector": embedding,
                        "chunk_text": chunk,
                        "frame_id": frame_id,
                        "timestamp": ts,
                        "app_name": app_name,
                        "window_title": win_title,
                    })
                vec_tbl.add(rows)
                print(f"embedded {len(rows)} chunks from frame {frame_id}", flush=True)

                prev_hash = h
                time.sleep(5)


if __name__ == "__main__":
    engine = CaptureEngine()
    engine.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
        print("stopped", flush=True)
