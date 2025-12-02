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

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [trending, setTrending] = useState([]);
  const [trendGraph, setTrendGraph] = useState([]);
  const [serverQueryInfo, setServerQueryInfo] = useState(null);
const [mode, setMode] = useState("keyword"); // 'keyword' | 'semantic'

  // Load trending
  const loadTrending = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5000/trending");
      const data = await res.json();
      setTrending(data);
    } catch (err) {
      console.log("Failed to fetch trending");
    }
  };

  const loadGraph = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5000/trending_graph");
      const data = await res.json();
      setTrendGraph(data);
    } catch (err) {
      console.log("Failed to fetch graph");
    }
  };

  useEffect(() => {
    loadTrending();
    loadGraph();
  }, []);
<div className="flex justify-center gap-4 mb-3">
  <button
    className={`px-4 py-1 rounded-full text-sm ${
      mode === "keyword" ? "bg-blue-600 text-white" : "bg-gray-200"
    }`}
    onClick={() => setMode("keyword")}
  >
    Keyword
  </button>
  <button
    className={`px-4 py-1 rounded-full text-sm ${
      mode === "semantic" ? "bg-blue-600 text-white" : "bg-gray-200"
    }`}
    onClick={() => setMode("semantic")}
  >
    Semantic
  </button>
</div>

  // Search
  const search = async () => {
  if (!query.trim()) return;
  const endpoint =
    mode === "semantic" ? "search_semantic" : "search";

  const res = await fetch(`http://127.0.0.1:5000/${endpoint}?q=${query}`);
  const data = await res.json();

  if (Array.isArray(data)) {
    setResults(data);                      // semantic
  } else {
    setResults(data.results || []);        // keyword
  }
};


  // Autocomplete
  const autocomplete = async (value) => {
    setQuery(value);
    if (!value.trim()) return setSuggestions([]);

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
    <div className="min-h-screen px-8 py-10 bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-white transition-all duration-300">
      {/* Title */}
      <h1 className="text-4xl font-bold text-center mb-6">
        🔍 Mini Search Engine
      </h1>

      {/* Search UI */}
      <div className="flex justify-center gap-3 relative">
        
        <input
          value={query}
          onChange={(e) => autocomplete(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="Search anything..."
          className="w-1/2 px-5 py-3 rounded-full border shadow-md text-black text-lg focus:ring-2 focus:ring-blue-500 outline-none"
        />

        <button
          onClick={search}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-semibold transition-all"
        >
          Search
        </button>
          
  

        {/* Suggestions dropdown */}
        {suggestions.length > 0 && (
          <ul className="absolute top-14 w-1/2 bg-white text-black rounded-xl shadow-lg max-h-60 overflow-y-auto p-2">
            {suggestions.map((s, i) => (
              <li
                key={i}
                onClick={() => {
                  setQuery(s);
                  setSuggestions([]);
                }}
                className="p-3 cursor-pointer hover:bg-gray-200 rounded-lg"
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Trending Section */}
      <div className="mt-10 text-center">
        <h2 className="text-2xl font-semibold mb-3">🔥 Trending Searches</h2>
        <div className="flex justify-center gap-3 flex-wrap">
          {trending.map((t, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(t);
                search();
              }}
              className="bg-white dark:bg-gray-700 dark:text-white text-black text-sm px-4 py-2 rounded-full shadow hover:scale-105 transition duration-300"
            >
              {t}
            </button>
          ))}
        </div>
      </div>
<a
  href={r.url}
  target="_blank"
  rel="noopener noreferrer"
  className="text-xl font-bold text-blue-700 dark:text-blue-400"
>
  {r.title}
</a>

      {/* Trend graph */}
      <div className="mt-10 p-5 bg-white dark:bg-gray-800 rounded-xl shadow-xl">
        <Line
          data={{
            labels: trendGraph.map((v) => v.term),
            datasets: [
              {
                label: "Search Count",
                data: trendGraph.map((v) => v.count),
                borderColor: "#0078ff",
                tension: 0.4,
              },
            ],
          }}
        />
      </div>
{serverQueryInfo?.corrected && (
  <div className="mt-4 text-center text-sm">
    Did you mean{" "}
    <button
      className="text-blue-600 underline"
      onClick={() => {
        setQuery(serverQueryInfo.usedQuery);
        search();
      }}
    >
      {serverQueryInfo.usedQuery}
    </button>
    ?
  </div>
)}

      {/* Results */}
      <div className="mt-10">
        {results.map((r, i) => (
          <div
            key={i}
            className="p-6 mb-6 bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl transition-transform hover:scale-[1.02]"
          >
            <a href={r.url} target="_blank" className="text-xl font-bold text-blue-700 dark:text-blue-400">
              {r.title}
            </a>
            <p className="text-green-600">{r.url}</p>
            <p
              dangerouslySetInnerHTML={{ __html: highlight(r.snippet, query) }}
              className="mt-2 text-lg"
            />
            <small className="opacity-60">Score: {r.score?.toFixed(4)}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
