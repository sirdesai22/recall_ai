import { useState, useEffect } from "react";

function App() {
  const [query, setQuery] = useState("");
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
    try {
      const res = await fetch("http://localhost:8765/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
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
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          placeholder="Search your screen..."
          style={{ flex: 1 }}
        />
        <button onClick={togglePause}>
          {paused ? "Resume" : "Pause"}
        </button>
        <span>{paused ? "paused" : "capturing"}</span>
      </div>
      {loading && <p>loading...</p>}
      {results.map((r, i) => (
        <div key={i}>
          <p>{new Date(r.timestamp * 1000).toLocaleString()}</p>
          <p>{r.app_name}</p>
          <p>{r.chunk_text}</p>
        </div>
      ))}
    </div>
  );
}

export default App;
