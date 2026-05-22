from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query import search
from capture import CaptureEngine

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


@app.get("/status")
def status():
    return {"status": "ok"}


@app.post("/search")
def search_route(req: SearchRequest):
    results = search(req.query)
    return {"results": results}


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


if __name__ == "__main__":
    import uvicorn
    engine.start()
    uvicorn.run(app, host="0.0.0.0", port=8765)
