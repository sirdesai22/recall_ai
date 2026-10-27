import threading, time, datetime, sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query import search
from capture import CaptureEngine, DB_PATH
from compress import run_compression, purge_range

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = CaptureEngine()


class SearchRequest(BaseModel):
    query: str
    start_date: str | None = None
    end_date: str | None = None


class PurgeRequest(BaseModel):
    start_date: str
    end_date: str


def seconds_until_midnight():
    now = datetime.datetime.now()
    midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - now).total_seconds()


def compression_loop():
    while True:
        delay = seconds_until_midnight()
        print(f"[compress] sleeping {delay:.0f}s until midnight", flush=True)
        time.sleep(delay)
        try:
            run_compression()
        except Exception as e:
            print(f"[compress] error: {e}", flush=True)


@app.get("/status")
def status():
    return {"status": "ok"}


@app.post("/search")
def search_route(req: SearchRequest):
    start_ts = end_ts = None
    if req.start_date and req.end_date:
        start_ts = datetime.datetime.fromisoformat(req.start_date).timestamp()
        # end date is inclusive: advance to end of that day
        end_dt = datetime.datetime.fromisoformat(req.end_date)
        end_ts = (end_dt + datetime.timedelta(days=1)).timestamp()
    return search(req.query, start_ts=start_ts, end_ts=end_ts)


@app.post("/pause")
def pause():
    if engine.paused:
        engine.resume()
        return {"paused": False}
    else:
        engine.pause()
        return {"paused": True}


def frame_count():
    try:
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return 0


@app.get("/capture-status")
def capture_status():
    sr = engine.sensitive_reason
    if sr:
        return {"paused": True, "paused_reason": sr, "frame_count": frame_count()}
    return {"paused": engine.paused, "frame_count": frame_count()}


@app.post("/purge")
def purge(req: PurgeRequest):
    start = datetime.datetime.fromisoformat(req.start_date).timestamp()
    end = datetime.datetime.fromisoformat(req.end_date).timestamp()
    purge_range(start, end)
    return {"deleted": True}


if __name__ == "__main__":
    import uvicorn
    engine.start()
    t = threading.Thread(target=compression_loop, daemon=True)
    t.start()
    uvicorn.run(app, host="127.0.0.1", port=8765)
