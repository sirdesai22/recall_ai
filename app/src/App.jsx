import { useState, useEffect, useRef } from "react";
import { FiSearch, FiGlobe, FiClock, FiFile, FiSliders, FiTrash2, FiCpu, FiPause, FiPlay } from "react-icons/fi";

const mono = { fontFamily: "'JetBrains Mono', monospace" };

function formatTS(ts) {
  const d = new Date(ts * 1000);
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const h = d.getHours(), m = d.getMinutes();
  const ampm = h >= 12 ? "PM" : "AM";
  const hh = h % 12 || 12;
  return `${days[d.getDay()]} ${d.getDate()} ${months[d.getMonth()]} · ${hh}:${String(m).padStart(2, "0")} ${ampm}`;
}

function extractSnippet(raw) {
  const lines = raw.split("\n").map(l => l.trim()).filter(l => l.length > 20);
  for (const line of lines) {
    const digitRatio = (line.match(/\d/g) || []).length / line.length;
    const symbolRatio = (line.match(/[^a-zA-Z0-9\s]/g) || []).length / line.length;
    if (digitRatio < 0.6 && symbolRatio < 0.4) return line;
  }
  return lines[0] || "";
}

function GhostCard() {
  return (
    <div style={{ background: "#16162A", border: "1px solid #252540", borderRadius: 12, padding: 16 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        <div style={{ width: 80, height: 10, background: "#1E1E3A", borderRadius: 4 }} />
        <div style={{ width: 120, height: 10, background: "#1E1E3A", borderRadius: 4 }} />
      </div>
      <div style={{ width: "100%", height: 10, background: "#1E1E3A", borderRadius: 4, marginBottom: 6 }} />
      <div style={{ width: "75%", height: 10, background: "#1E1E3A", borderRadius: 4 }} />
    </div>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [paused, setPaused] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [searched, setSearched] = useState(false);
  const [showFilter, setShowFilter] = useState(false);
  const [filterStart, setFilterStart] = useState("");
  const [filterEnd, setFilterEnd] = useState("");
  const [showPurge, setShowPurge] = useState(false);
  const [purgeStart, setPurgeStart] = useState("");
  const [purgeEnd, setPurgeEnd] = useState("");
  const [shifted, setShifted] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:8765/capture-status").then(r => r.json()).then(d => {
      setPaused(d.paused);
      if (d.frame_count !== undefined) setFrameCount(d.frame_count);
    }).catch(() => {});
    const id = setInterval(() => {
      fetch("http://localhost:8765/capture-status").then(r => r.json()).then(d => {
        setPaused(d.paused);
        if (d.frame_count !== undefined) setFrameCount(d.frame_count);
      }).catch(() => {});
    }, 30000);
    return () => clearInterval(id);
  }, []);

  async function doSearch() {
    if (!query.trim()) return;
    setShifted(true);
    const parts = [query.trim()];
    if (filterStart) parts.push(`after:${filterStart}`);
    if (filterEnd) parts.push(`before:${filterEnd}`);
    setLoading(true); setAnswer(""); setResults([]); setSearched(true);
    try {
      const res = await fetch("http://localhost:8765/search", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
      });
      const data = await res.json();
      setAnswer(data.answer || "");
      setResults(data.results || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }

  async function togglePause() {
    try {
      const res = await fetch("http://localhost:8765/pause", { method: "POST" });
      const data = await res.json();
      setPaused(data.paused);
    } catch (err) { console.error(err); }
  }

  async function doPurge() {
    if (!purgeStart || !purgeEnd) return;
    try {
      await fetch("http://localhost:8765/purge", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start_date: purgeStart, end_date: purgeEnd }),
      });
      setShowPurge(false);
    } catch (err) { console.error(err); }
  }

  const typing = query.length > 0;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "20px 20px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "linear-gradient(135deg, #6C63FF, #A78BFA)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <FiCpu size={16} color="white" />
          </div>
          <span style={{ fontSize: 13, fontWeight: 500, color: "#9B8FCC", letterSpacing: "0.04em" }}>RECALL</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={togglePause} style={{
            display: "flex", alignItems: "center", gap: 6,
            background: paused ? "#1E1E3A" : "rgba(74,222,128,0.1)",
            border: paused ? "1px solid #2E2E4A" : "1px solid rgba(74,222,128,0.25)",
            borderRadius: 8, padding: "5px 10px", cursor: "pointer",
            ...mono, fontSize: 11, color: paused ? "#555570" : "#4ADE80",
          }}>
            {paused ? <FiPlay size={12} /> : <FiPause size={12} />}
            {paused ? "Resume" : "Pause"}
          </button>
          <span style={{ display: "flex", alignItems: "center", gap: 5, ...mono, fontSize: 11, color: "#555570" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: paused ? "#555570" : "#4ADE80", display: "inline-block" }} />
            {frameCount.toLocaleString()} moments
          </span>
        </div>
      </div>

      {/* Middle: search + results */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", transition: "all 0.4s ease", overflow: "hidden" }}>
        {/* Search bar wrapper */}
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          transition: "margin 0.4s ease, padding 0.4s ease",
          marginTop: shifted ? 16 : "auto",
          marginBottom: shifted ? 0 : "auto",
          padding: shifted ? "0 20px" : "0",
          width: "100%",
        }}>
          <div style={{ position: "relative", width: shifted ? "calc(100% - 40px)" : "60%", transition: "width 0.4s ease" }}>
            <div style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", display: "flex", pointerEvents: "none" }}>
              <FiSearch size={15} color="#6C63FF" />
            </div>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && doSearch()}
              placeholder="Ask anything about your screen history..."
              style={{
                width: "100%", background: "#1C1C2E", border: "1px solid #2E2E4A", borderRadius: 10,
                padding: "12px 40px", fontSize: 14, color: "#E0DEFF",
              }}
              onFocus={e => e.target.style.borderColor = "#6C63FF"}
              onBlur={e => e.target.style.borderColor = "#2E2E4A"}
            />
            {!typing && (
              <span style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", ...mono, fontSize: 11, color: "#444", pointerEvents: "none" }}>
                ↵ enter
              </span>
            )}
          </div>
        </div>

        {/* Filter / Purge bars */}
        {showFilter && (
          <div style={{ margin: "12px 20px 0", padding: 12, background: "#16162A", border: "1px solid #252540", borderRadius: 10, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ ...mono, fontSize: 11, color: "#555570" }}>From</span>
            <input type="date" value={filterStart} onChange={e => setFilterStart(e.target.value)}
              style={{ background: "#1C1C2E", border: "1px solid #2E2E4A", borderRadius: 6, padding: "4px 8px", fontSize: 12, color: "#E0DEFF", fontFamily: "'JetBrains Mono', monospace" }} />
            <span style={{ ...mono, fontSize: 11, color: "#555570" }}>to</span>
            <input type="date" value={filterEnd} onChange={e => setFilterEnd(e.target.value)}
              style={{ background: "#1C1C2E", border: "1px solid #2E2E4A", borderRadius: 6, padding: "4px 8px", fontSize: 12, color: "#E0DEFF", fontFamily: "'JetBrains Mono', monospace" }} />
            <button onClick={() => { setShowFilter(false); setFilterStart(""); setFilterEnd(""); }}
              style={{ ...mono, fontSize: 11, color: "#555570", marginLeft: "auto", cursor: "pointer", background: "none", border: "none" }}>Clear</button>
          </div>
        )}
        {showPurge && (
          <div style={{ margin: "12px 20px 0", padding: 12, background: "#16162A", border: "1px solid #252540", borderRadius: 10, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ ...mono, fontSize: 11, color: "#555570" }}>Purge from</span>
            <input type="date" value={purgeStart} onChange={e => setPurgeStart(e.target.value)}
              style={{ background: "#1C1C2E", border: "1px solid #2E2E4A", borderRadius: 6, padding: "4px 8px", fontSize: 12, color: "#E0DEFF", fontFamily: "'JetBrains Mono', monospace" }} />
            <span style={{ ...mono, fontSize: 11, color: "#555570" }}>to</span>
            <input type="date" value={purgeEnd} onChange={e => setPurgeEnd(e.target.value)}
              style={{ background: "#1C1C2E", border: "1px solid #2E2E4A", borderRadius: 6, padding: "4px 8px", fontSize: 12, color: "#E0DEFF", fontFamily: "'JetBrains Mono', monospace" }} />
            <button onClick={doPurge}
              style={{ ...mono, fontSize: 11, color: "#6C63FF", marginLeft: "auto", cursor: "pointer", background: "none", border: "none" }}>Delete</button>
            <button onClick={() => setShowPurge(false)}
              style={{ ...mono, fontSize: 11, color: "#555570", cursor: "pointer", background: "none", border: "none" }}>Cancel</button>
          </div>
        )}

        {/* Results */}
        <div style={{
          flex: 1, overflowY: "auto", padding: shifted ? "16px 20px 0" : "0",
          transition: "padding 0.4s ease, opacity 0.4s ease",
          opacity: shifted ? 1 : 0,
        }}>
          {loading && (
            <>
              <div style={{ textAlign: "center", ...mono, fontSize: 12, color: "#6C63FF", marginBottom: 12 }}>
                Searching {frameCount.toLocaleString() || "..."} moments...
              </div>
              <GhostCard />
              <div style={{ height: 10 }} />
              <GhostCard />
            </>
          )}

          {!loading && searched && !answer && !results.length && (
            <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6 }}>
              <FiSearch size={32} color="#2E2E4A" />
              <div style={{ fontSize: 14, color: "#3A3A5C", fontWeight: 500 }}>Nothing found</div>
              <div style={{ fontSize: 12, color: "#2E2E4A" }}>Try rephrasing or a different time range</div>
            </div>
          )}

          {!loading && searched && results.length > 0 && (
            <div style={{ marginBottom: 8, ...mono, fontSize: 11, color: "#4A4A6A", letterSpacing: "0.06em" }}>
              {results.length} RESULT(S) FOUND
            </div>
          )}

          {!loading && answer && (
            <div style={{ background: "#16162A", border: "1px solid #252540", borderRadius: 12, padding: 16, marginBottom: 10 }}>
              <div style={{ fontSize: 14, color: "#C4BEFF", lineHeight: 1.65, marginBottom: 14, whiteSpace: "pre-wrap" }}>{answer}</div>
            </div>
          )}

        {!loading && results.map((r, i) => {
          const lines = (r.chunk_text || r.raw_text || "").split("\n").filter(l => l.trim().length > 20);
          const displayLine = lines[0] || "";
          return (
            <div key={i} style={{ background: "#16162A", border: "1px solid #252540", borderRadius: 12, padding: 16, marginBottom: 10 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 5, background: "#1E1E3A", borderRadius: 6, padding: "4px 8px" }}>
                  <FiGlobe size={12} color="#6C63FF" />
                  <span style={{ ...mono, fontSize: 11, color: "#6C63FF" }}>{r.app_name}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, background: "#1E1E3A", borderRadius: 6, padding: "4px 8px" }}>
                  <FiClock size={12} color="#555570" />
                  <span style={{ ...mono, fontSize: 11, color: "#555570" }}>{formatTS(r.timestamp)}</span>
                </div>
              </div>
              <div style={{ borderTop: "1px solid #1E1E3A", paddingTop: 12, display: "flex", gap: 8, alignItems: "flex-start" }}>
                <FiFile size={13} color="#3A3A5C" />
                <span style={{ ...mono, fontSize: 12, color: "#3A3A5C", lineHeight: 1.6 }}>{displayLine.slice(0, 200)}</span>
              </div>
            </div>
          );
        })}
      </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: "1px solid #1A1A2E", padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: 16 }}>
          <div onClick={() => setShowFilter(v => !v)} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: showFilter ? "#6C63FF" : "#3A3A5C", cursor: "pointer" }}>
            <FiSliders size={12} />
            <span>Filter</span>
          </div>
          <div onClick={() => setShowPurge(v => !v)} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: showPurge ? "#6C63FF" : "#3A3A5C", cursor: "pointer" }}>
            <FiTrash2 size={12} />
            <span>Purge range</span>
          </div>
        </div>
        <span style={{ ...mono, fontSize: 11, color: "#2E2E4A" }}>recall v0.1</span>
      </div>
    </div>
  );
}

export default App;
