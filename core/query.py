import sys, datetime, lancedb, ollama
from temporal import parse_time_range, strip_time_expression

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"
LANCEDB_PATH = "lancedb"


def embed_text(text):
    response = ollama.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def search(query, top_k=5):
    time_range = parse_time_range(query)
    clean_query = strip_time_expression(query)

    db = lancedb.connect(LANCEDB_PATH)
    tbl = db.open_table("chunks")
    vec = embed_text(clean_query)

    search_builder = tbl.search(vec).limit(top_k * 3)
    if time_range:
        start, end = time_range
        search_builder = search_builder.where(
            f"timestamp >= {start} AND timestamp <= {end}"
        )
    results = search_builder.to_list()

    seen = {}
    for r in results:
        fid = r["frame_id"]
        if fid not in seen:
            seen[fid] = r
    results = list(seen.values())[:top_k]

    answer = generate_answer(query, results, time_range) if results else "No relevant results found."

    return {"answer": answer, "results": results}


def generate_answer(query, results, time_range):
    ctx = ""
    for r in results:
        ts = datetime.datetime.fromtimestamp(r["timestamp"]).strftime("%a %b %d at %I:%M%p")
        ctx += f"[{ts} | {r['app_name']}]\n{r['chunk_text']}\n\n"

    time_hint = ""
    if time_range:
        start = datetime.datetime.fromtimestamp(time_range[0]).strftime("%A %B %d")
        end = datetime.datetime.fromtimestamp(time_range[1]).strftime("%A %B %d")
        if start == end:
            time_hint = f"The user is asking about content from {start}. Only reference results from this period."
        else:
            time_hint = f"The user is asking about content from {start} to {end}. Only reference results from this period."

    system = (
        "You are Recall, an AI assistant that answers questions about what the user saw on their screen. "
        "You are given timestamped OCR text captured from their screen, along with the app name. "
        "Answer concisely from the provided context. "
        "If the retrieved content does not appear relevant to the query, say so — do not fabricate an answer."
    )

    prompt = f"""Query: {query}

{time_hint}

Retrieved screen content:
{ctx}

Answer the query based on the retrieved content above. Reference specific timestamps and app names when possible."""
    if not time_hint:
        prompt = f"""Query: {query}

Retrieved screen content:
{ctx}

Answer the query based on the retrieved content above. Reference specific timestamps and app names when possible."""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"].strip()


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "what was on my screen"
    print(f'Query: "{query}"\n')
    result = search(query)
    print(f"Answer:\n{result['answer']}\n")
    print("Sources:")
    for r in result["results"]:
        print(f"  frame_id={r['frame_id']} | app={r['app_name']} | dist={r['_distance']:.3f}")
