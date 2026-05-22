import { useState, useEffect } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8765/capture-status")
      .then((r) => r.json())
      .then((d) => setPaused(d.paused))
      .catch(() => {});
  }, []);

  async function doSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer("");
    setResults([]);
    try {
      const res = await fetch("http://localhost:8765/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setAnswer(data.answer || "");
      setResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function togglePause() {
    try {
      const res = await fetch("http://localhost:8765/pause", { method: "POST" });
      const data = await res.json();
      setPaused(data.paused);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          placeholder="Search your screen..."
          style={{ flex: 1, padding: "8px 12px", fontSize: 16 }}
        />
        <button onClick={togglePause}>
          {paused ? "Resume" : "Pause"}
        </button>
        <span style={{ fontSize: 13, color: paused ? "#999" : "#4caf50" }}>
          {paused ? "paused" : "capturing"}
        </span>
      </div>
      {loading && <p>searching...</p>}
      {answer && (
        <div style={{ background: "#f5f5f5", padding: 16, borderRadius: 8, marginBottom: 16, whiteSpace: "pre-wrap" }}>
          {answer}
        </div>
      )}
      {results.map((r, i) => (
        <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid #eee", fontSize: 14 }}>
          <span style={{ color: "#666" }}>
            {new Date(r.timestamp * 1000).toLocaleString()} &mdash; {r.app_name}
          </span>
          <p style={{ margin: "4px 0", color: "#333" }}>{r.chunk_text}</p>
        </div>
      ))}
    </div>
  );
}

export default App;
