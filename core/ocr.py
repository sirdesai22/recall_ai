import re


def clean_text(raw: str) -> str:
    lines = [l.strip() for l in raw.split("\n")]
    lines = [l for l in lines if len(l) >= 4]
    lines = [l for l in lines if not l.isdigit()]
    lines = [l for l in lines if not re.fullmatch(r"[^\w\s]+", l)]
    seen = set()
    deduped = []
    for l in lines:
        if l not in seen:
            seen.add(l)
            deduped.append(l)
    return " ".join(deduped)


def chunk_text(text: str, window: int = 150, overlap: int = 30) -> list[str]:
    words = text.split()
    if len(words) <= window:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + window
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += window - overlap
    return chunks
