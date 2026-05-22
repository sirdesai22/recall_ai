import threading, time, datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query import search
from capture import CaptureEngine
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
    return search(req.query)


@app.post("/pause")
def pause():
    if engine.paused:
        engine.resume()
        return {"paused": False}
    else:
        engine.pause()
        return {"paused": True}


@app.get("/capture-status")
def capture_status():
    return {"paused": engine.paused}


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
    uvicorn.run(app, host="0.0.0.0", port=8765)
