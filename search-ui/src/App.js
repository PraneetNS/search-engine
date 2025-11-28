import { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  const search = async () => {
    const res = await fetch(`http://127.0.0.1:5000/search?q=${query}`);
    const data = await res.json();
    setResults(data);
  };

  const autocomplete = async (value) => {
    setQuery(value);
    if (!value) return setSuggestions([]);

    const res = await fetch(`http://127.0.0.1:5000/suggest?q=${value}`);
    const data = await res.json();
    setSuggestions(data);
  };

  const highlight = (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, "gi");
    return text.replace(regex, "<mark>$1</mark>");
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial", maxWidth: "800px", margin: "auto" }}>
      <h1 style={{ textAlign: "center" }}>Mini Search Engine</h1>

      <div style={{ display: "flex", justifyContent: "center", marginBottom: "10px" }}>
        <input
          value={query}
          onChange={(e) => autocomplete(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="Search..."
          style={{
            padding: "12px",
            width: "400px",
            fontSize: "18px",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        />

        <button
          onClick={search}
          style={{
            padding: "12px 20px",
            marginLeft: "10px",
            borderRadius: "8px",
            fontSize: "16px",
            backgroundColor: "#0078ff",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          Search
        </button>
      </div>

      <ul
        style={{
          listStyle: "none",
          paddingLeft: 0,
          width: "400px",
          margin: "auto",
          backgroundColor: "white",
          borderRadius: "8px",
          border: "1px solid #ddd",
        }}
      >
        {suggestions.map((s, i) => (
          <li
            key={i}
            onClick={() => {
              setQuery(s);
              setSuggestions([]);
            }}
            style={{ padding: "10px", cursor: "pointer" }}
          >
            {s}
          </li>
        ))}
      </ul>

      <div style={{ marginTop: "30px" }}>
        {results.map((r, i) => (
          <div
            key={i}
            style={{
              marginBottom: "20px",
              padding: "15px",
              borderRadius: "10px",
              backgroundColor: "white",
              boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
            }}
          >
            <a
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: "20px", color: "#1a0dab", textDecoration: "none" }}
            >
              {r.title}
            </a>

            <p style={{ color: "green", fontSize: "14px", margin: 0 }}>{r.url}</p>

            <p
              style={{ fontSize: "16px" }}
              dangerouslySetInnerHTML={{ __html: highlight(r.snippet, query) }}
            />

            <small style={{ opacity: 0.5 }}>score: {r.score.toFixed(4)}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
