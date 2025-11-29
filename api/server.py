import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import Counter
import math

from crawler.crawler import Crawler
from indexer.inverted_index import InvertedIndex
from indexer.storage import save_index, load_index
from search.query import search, build_snippet
from search.autocomplete import Trie

# ---- Optional Redis (safe fallback) ----
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_enabled = True
    print("Redis enabled ✔")
except Exception:
    print("⚠ Redis unavailable — using memory only")
    r = None
    redis_enabled = False

app = Flask(__name__)
CORS(app)

# ---------------------
# LOAD INDEX + DOCS
# ---------------------
idx = InvertedIndex()
docs = {}

try:
    index_data, doc_lengths, stored_docs = load_index()
    idx.index = index_data
    idx.doc_lengths = doc_lengths
    docs = stored_docs
    print("Loaded index & docs from storage.")
except Exception:
    print("Index not found — crawling Wikipedia...")
    crawler = Crawler(max_pages=50)
    docs = crawler.crawl("https://en.wikipedia.org/wiki/India")

    for url, data in docs.items():
        idx.add_document(url, data["text"])

    save_index(idx.index, idx.doc_lengths, docs)
    print("Index & docs saved.")

print("DOCS COUNT:", len(docs))

# ---------------------
# AUTOCOMPLETE TRIE
# ---------------------
trie = Trie()
for word in idx.index.keys():
    trie.insert(word)
print("Trie loaded with", len(idx.index), "words.")

# ---------------------
# Trending & history
# ---------------------
trending_storage = {}      # query -> count
user_history = {}          # ip -> [query, ...]

# ---------------------
# Categories & semantic vectors
# ---------------------
categories = set()
doc_vectors = {}           # url -> {word: tfidf}
N_DOCS = max(len(docs), 1)


def build_doc_vectors():
    """Lightweight 'semantic' vectors using TF-IDF; no transformers."""
    global categories, doc_vectors

    for url, data in docs.items():
        text = data.get("text", "")
        cat = data.get("category")
        if cat:
            categories.add(cat.lower())

        words = text.lower().split()
        if not words:
            continue

        counts = Counter(words)
        doc_len = len(words)
        vec = {}

        for w, freq in counts.items():
            if w in idx.index:
                tf = freq / doc_len
                df = len(idx.index[w])
                if df == 0:
                    continue
                idf = math.log(N_DOCS / df)
                vec[w] = tf * idf

        if vec:
            doc_vectors[url] = vec

    print(f"Semantic vectors built for {len(doc_vectors)} docs.")
    print(f"Categories detected: {sorted(list(categories))}")


def build_query_vector(query: str):
    words = query.lower().split()
    if not words:
        return {}

    counts = Counter(words)
    q_len = len(words)
    vec = {}
    for w, freq in counts.items():
        if w in idx.index:
            tf = freq / q_len
            df = len(idx.index[w])
            if df == 0:
                continue
            idf = math.log(N_DOCS / df)
            vec[w] = tf * idf
    return vec


def cosine_similarity(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(v1[w] * v2.get(w, 0.0) for w in v1)
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if not n1 or not n2:
        return 0.0
    return dot / (n1 * n2)


build_doc_vectors()

# ---------------------
# Query tracking
# ---------------------
@app.after_request
def track_queries(response):
    query = request.args.get("q", "").strip()
    if query:
        # in-memory trending
        trending_storage[query] = trending_storage.get(query, 0) + 1

        # per-user history
        user = request.remote_addr
        user_history[user] = user_history.get(user, []) + [query]

        # optional Redis
        if redis_enabled:
            try:
                r.zincrby("trending_searches", 1, query)
                r.zincrby(f"user:{user}:history", 1, query)
            except Exception:
                print("⚠ Redis update failed; ignoring.")
    return response


# ---------------------
# ROUTES
# ---------------------
@app.get("/")
def home():
    return {"message": "Mini Search Engine Running 🚀"}


@app.get("/search")
def perform_search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip().lower()

    # filter docs by category if provided
    filtered_docs = docs
    if category:
        filtered_docs = {
            url: data
            for url, data in docs.items()
            if data.get("category", "").lower() == category
        }

    total = max(len(filtered_docs), 1)
    results = search(query, idx, filtered_docs, total_docs=total)
    return jsonify(results[:50])  # backend cap; frontend paginates


@app.get("/search_semantic")
def perform_search_semantic():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    q_vec = build_query_vector(query)
    scores = []

    for url, d_vec in doc_vectors.items():
        sim = cosine_similarity(q_vec, d_vec)
        if sim > 0:
            scores.append((url, sim))

    scores.sort(key=lambda x: x[1], reverse=True)

    results = []
    for url, score in scores[:50]:
        page = docs.get(url, {})
        snippet = build_snippet(page.get("text", ""), query)
        results.append({
            "url": url,
            "title": page.get("title", url),
            "snippet": snippet,
            "image": page.get("image"),
            "score": float(score),
        })

    return jsonify(results)


@app.get("/categories")
def get_categories():
    return jsonify(sorted(list(categories)))


@app.get("/suggest")
def suggest():
    prefix = request.args.get("q", "")
    suggestions = trie.autocomplete(prefix)
    return jsonify(suggestions[:10])


@app.get("/trending")
def trending_list():
    ordered = sorted(trending_storage.items(), key=lambda x: x[1], reverse=True)
    return jsonify([term for term, count in ordered][:10])


@app.get("/trending_graph")
def trending_graph():
    ordered = sorted(trending_storage.items(), key=lambda x: x[1], reverse=True)
    graph = [{"term": term, "count": count} for term, count in ordered]
    return jsonify(graph[:10])


@app.get("/recommended")
def recommended():
    user = request.remote_addr
    history = user_history.get(user, [])
    # keep only recent unique entries
    seen = set()
    unique_recent = []
    for q in reversed(history):
        if q not in seen:
            seen.add(q)
            unique_recent.append(q)
        if len(unique_recent) == 5:
            break
    return jsonify(list(reversed(unique_recent)))


if __name__ == "__main__":
    app.run(debug=True)
