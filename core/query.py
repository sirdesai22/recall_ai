import sys, lancedb, ollama

EMBED_MODEL = "nomic-embed-text"
LANCEDB_PATH = "lancedb"


def embed_text(text):
    response = ollama.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def search(query, top_k=5):
    db = lancedb.connect(LANCEDB_PATH)
    tbl = db.open_table("chunks")
    vec = embed_text(query)
    results = tbl.search(vec).limit(top_k * 3).to_list()
    seen = {}
    for r in results:
        fid = r["frame_id"]
        if fid not in seen:
            seen[fid] = r
    return list(seen.values())[:top_k]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "what was on my screen"
    print(f'Query: "{query}"\n')
    results = search(query)
    for r in results:
        print(f"--- frame_id={r['frame_id']} | dist={r['_distance']:.4f} | app={r['app_name']} ---")
        print(f"timestamp: {r['timestamp']}")
        print(f"chunk: {r['chunk_text'][:200].strip()}")
        print()
