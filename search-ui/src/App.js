import { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const API_BASE = "http://127.0.0.1:5000";

function App() {
  const [user, setUser] = useState(() => localStorage.getItem("user") || "");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [semanticResults, setSemanticResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [trending, setTrending] = useState([]);
  const [trendGraph, setTrendGraph] = useState([]);
  const [categories, setCategories] = useState([]);
  const [history, setHistory] = useState([]);

  const [selectedCategory, setSelectedCategory] = useState("");
  const [activeTab, setActiveTab] = useState("all"); // all | semantic | images | trending
  const [visibleCount, setVisibleCount] = useState(10);

  const userParam = user ? `&user=${encodeURIComponent(user)}` : "";

  // -------------- LOAD AUX DATA --------------
  const loadTrending = async () => {
    const res = await fetch(`${API_BASE}/trending`);
    setTrending(await res.json());
  };

  const loadGraph = async () => {
    const res = await fetch(`${API_BASE}/trending_graph`);
    setTrendGraph(await res.json());
  };

  const loadCategories = async () => {
    const res = await fetch(`${API_BASE}/categories`);
    setCategories(await res.json());
  };

  const loadHistory = async () => {
    const res = await fetch(`${API_BASE}/user_history?user=${encodeURIComponent(user || "guest")}`);
    setHistory(await res.json());
  };

  useEffect(() => {
    loadTrending();
    loadGraph();
    loadCategories();
    if (user) loadHistory();
    // eslint-disable-next-line
  }, [user]);

  // -------------- USER SAVE --------------
  const saveUser = () => {
    localStorage.setItem("user", user);
    loadHistory();
  };

  // -------------- SEARCH --------------
  const search = async () => {
    if (!query.trim()) return;

    const params = new URLSearchParams({ q: query });
    if (activeTab === "all" && selectedCategory) {
      params.append("category", selectedCategory);
    }
    if (user) {
      params.append("user", user);
    }

    if (activeTab === "semantic") {
      const res = await fetch(`${API_BASE}/search_semantic?${params.toString()}`);
      const data = await res.json();
      setSemanticResults(data);
    } else {
      const res = await fetch(`${API_BASE}/search?${params.toString()}`);
      const data = await res.json();
      setResults(data);
    }

    setVisibleCount(10);
    await loadTrending();
    await loadGraph();
    if (user) await loadHistory();
  };

  // -------------- AUTOCOMPLETE --------------
  const autocomplete = async (value) => {
    setQuery(value);
    if (!value.trim()) return setSuggestions([]);

    const res = await fetch(
      `${API_BASE}/suggest?q=${encodeURIComponent(value)}${userParam}`
    );
    setSuggestions(await res.json());
  };

  // -------------- VOICE SEARCH --------------
  const startVoiceSearch = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice search not supported in this browser.");
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = "en-IN";
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setQuery(text);
    };
    rec.start();
  };

  const highlight = (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, "gi");
    return text.replace(regex, "<mark>$1</mark>");
  };

  // -------------- RESULT SELECTION --------------
  let current = activeTab === "semantic" ? semanticResults : results;
  if (activeTab === "images") {
    current = current.filter((r) => r.image);
  }
  if (activeTab === "trending") {
    current = []; // trending tab only shows trending info
  }
  const slicedResults = current.slice(0, visibleCount);

  return (
    <div
      style={{
        padding: "30px 20px 60px",
        fontFamily: "Inter, Arial",
        maxWidth: "1000px",
        margin: "auto",
      }}
    >
      <h1 style={{ textAlign: "center", fontSize: "40px", marginBottom: "5px" }}>
        🔍 Mini Search Engine
      </h1>

      {/* USER / LOGIN ROW */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "8px",
          marginBottom: "15px",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: "14px" }}>User:</span>
        <input
          value={user}
          onChange={(e) => setUser(e.target.value)}
          placeholder="your-name or email"
          style={{
            padding: "6px 10px",
            borderRadius: "16px",
            border: "1px solid #ccc",
            minWidth: "200px",
          }}
        />
        <button
          onClick={saveUser}
          style={{
            padding: "6px 12px",
            borderRadius: "16px",
            border: "none",
            backgroundColor: "#0078ff",
            color: "white",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          Save
        </button>
      </div>

      {/* TABS */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "12px",
          marginBottom: "15px",
        }}
      >
        {[
          { id: "all", label: "All" },
          { id: "semantic", label: "Semantic" },
          { id: "images", label: "Images" },
          { id: "trending", label: "Trending" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "8px 16px",
              borderRadius: "999px",
              border: "none",
              cursor: "pointer",
              backgroundColor:
                activeTab === tab.id ? "#0078ff" : "rgba(0,0,0,0.05)",
              color: activeTab === tab.id ? "white" : "black",
              fontWeight: 500,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* SEARCH BAR + CATEGORY + VOICE */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          position: "relative",
          gap: "10px",
          alignItems: "center",
        }}
      >
        <input
          value={query}
          onChange={(e) => autocomplete(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="Search anything..."
          style={{
            padding: "13px 18px",
            width: "450px",
            fontSize: "18px",
            borderRadius: "30px",
            border: "1px solid #ddd",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        />

        <button
          onClick={startVoiceSearch}
          title="Voice search"
          style={{
            padding: "10px 12px",
            borderRadius: "50%",
            border: "none",
            cursor: "pointer",
          }}
        >
          🎤
        </button>

        {activeTab === "all" && (
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: "10px",
              borderRadius: "20px",
              border: "1px solid #ddd",
            }}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        )}

        <button
          onClick={search}
          style={{
            padding: "12px 22px",
            borderRadius: "30px",
            fontSize: "16px",
            backgroundColor: "#0078ff",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          Search
        </button>

        {suggestions.length > 0 && (
          <ul
            style={{
              listStyle: "none",
              position: "absolute",
              top: "52px",
              width: "450px",
              backgroundColor: "white",
              borderRadius: "8px",
              border: "1px solid #ddd",
              boxShadow: "0 4px 10px rgba(0,0,0,0.15)",
              maxHeight: "200px",
              overflowY: "auto",
              padding: "10px 0",
              zIndex: 10,
            }}
          >
            {suggestions.map((s, i) => (
              <li
                key={i}
                onClick={() => {
                  setQuery(s);
                  setSuggestions([]);
                }}
                style={{
                  padding: "10px 15px",
                  cursor: "pointer",
                  fontSize: "17px",
                }}
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* PERSONALIZED HISTORY */}
      <div style={{ marginTop: "20px", textAlign: "center" }}>
        <h3>🕒 Your recent searches</h3>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >
          {history.map((h, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(h);
                search();
              }}
              style={{
                padding: "6px 12px",
                borderRadius: "16px",
                border: "none",
                backgroundColor: "#f3f3f3",
                cursor: "pointer",
                fontSize: "13px",
              }}
            >
              {h}
            </button>
          ))}
          {history.length === 0 && (
            <span style={{ fontSize: "13px", opacity: 0.7 }}>
              No history yet — try searching something 🙂
            </span>
          )}
        </div>
      </div>

      {/* TRENDING + GRAPH */}
      <div style={{ marginTop: "25px", textAlign: "center" }}>
        <h3>🔥 Trending Searches</h3>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "10px",
            flexWrap: "wrap",
            marginBottom: "15px",
          }}
        >
          {trending.map((t, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(t);
                search();
              }}
              style={{
                padding: "8px 14px",
                borderRadius: "20px",
                backgroundColor: "#eee",
                border: "none",
                cursor: "pointer",
              }}
            >
              {t}
            </button>
          ))}
        </div>

        <div style={{ maxWidth: "700px", margin: "0 auto" }}>
          <Line
            data={{
              labels: trendGraph.map((v) => v.term),
              datasets: [
                {
                  data: trendGraph.map((v) => v.count),
                  borderColor: "#0078ff",
                  tension: 0.4,
                },
              ],
            }}
          />
        </div>
      </div>

      {/* RESULTS */}
      {activeTab !== "trending" && (
        <div style={{ marginTop: "30px" }}>
          {slicedResults.map((r, i) => (
            <div
              key={i}
              style={{
                marginBottom: "25px",
                padding: "18px",
                borderRadius: "12px",
                backgroundColor: "white",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
              }}
            >
              {r.image && activeTab === "images" && (
                <img
                  src={r.image}
                  alt=""
                  style={{
                    width: "180px",
                    borderRadius: "10px",
                    marginBottom: "10px",
                    marginRight: "10px",
                    float: "right",
                  }}
                />
              )}

              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: "20px", color: "#1a0dab" }}
              >
                {r.title}
              </a>
              <p style={{ color: "green", fontSize: "14px", margin: "4px 0" }}>
                {r.url}
              </p>
              <p
                style={{ fontSize: "15px", lineHeight: 1.4 }}
                dangerouslySetInnerHTML={{
                  __html: highlight(r.snippet, query),
                }}
              />
              <small style={{ opacity: 0.6 }}>
                Score: {r.score ? r.score.toFixed(4) : "—"}
              </small>
            </div>
          ))}

          {current.length > visibleCount && (
            <div style={{ textAlign: "center", marginTop: "10px" }}>
              <button
                onClick={() => setVisibleCount((c) => c + 10)}
                style={{
                  padding: "10px 18px",
                  borderRadius: "20px",
                  border: "none",
                  cursor: "pointer",
                  backgroundColor: "#eee",
                }}
              >
                Load more
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
