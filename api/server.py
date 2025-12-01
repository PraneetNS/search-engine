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

# ---------------------------
# Optional Redis (still safe)
# ---------------------------
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_enabled = True
    print("Redis enabled ✔")
except Exception:
    print("⚠ Redis unavailable — using memory only")
    r = None
    redis_enabled = False

# ---------------------------
# Semantic Embeddings (MiniLM)
# ---------------------------
semantic_enabled = False
semantic_model = None
doc_embed_matrix = None
doc_embed_urls = []

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    print("Loading semantic model (MiniLM)...")
    semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    semantic_enabled = True
    print("Semantic model loaded ✔")
except Exception as e:
    print("⚠ Semantic model unavailable:", e)
    semantic_enabled = False

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
user_history = {}          # user_id -> [query, ...]
categories = set()         # optional categories
N_DOCS = max(len(docs), 1)


def get_user_id():
    """Use ?user= in query or fallback to IP."""
    uid = request.args.get("user") or request.headers.get("X-User")
    if not uid:
        uid = request.remote_addr or "anonymous"
    return uid


# ---------------------
# Lightweight category & semantic vectors (fallback if no MiniLM)
# ---------------------
doc_vectors = {}           # url -> {word: tfidf}  (used only if semantic model missing)


def build_doc_vectors_fallback():
    """TF-IDF vector fallback for semantic if MiniLM is not available."""
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

    print(f"Fallback semantic vectors (TF-IDF) built for {len(doc_vectors)} docs.")
    print(f"Categories detected: {sorted(list(categories))}")


def build_semantic_embeddings():
    """Build MiniLM embeddings once at startup if model is available."""
    global doc_embed_matrix, doc_embed_urls, categories

    if not semantic_enabled:
        print("Semantic disabled — using TF-IDF fallback only.")
        build_doc_vectors_fallback()
        return

    texts = []
    urls = []

    for url, data in docs.items():
        # short text for embedding (title + first 500 chars)
        text = (data.get("title", "") or "") + " " + (data.get("text", "")[:500] or "")
        texts.append(text)
        urls.append(url)

        cat = data.get("category")
        if cat:
            categories.add(cat.lower())

    if not texts:
        print("No texts available for semantic embeddings.")
        return

    print("Encoding documents for semantic search...")
    doc_embed_matrix = semantic_model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    doc_embed_urls = urls
    print(f"Semantic embeddings built for {len(doc_embed_urls)} docs.")
    print(f"Categories detected: {sorted(list(categories))}")


def semantic_search(query: str, top_k: int = 20):
    """Return list of semantic search results using MiniLM or fallback."""
    query = query.strip()
    if not query:
        return []

    # MiniLM path
    if semantic_enabled and doc_embed_matrix is not None:
        q_emb = semantic_model.encode([query], convert_to_numpy=True)[0]
        # cosine similarity
        norms = np.linalg.norm(doc_embed_matrix, axis=1) * (np.linalg.norm(q_emb) + 1e-10)
        sims = (doc_embed_matrix @ q_emb) / (norms + 1e-10)

        idxs = np.argsort(sims)[::-1][:top_k]
        results = []
        for i in idxs:
            url = doc_embed_urls[i]
            score = float(sims[i])
            page = docs.get(url, {})
            snippet = build_snippet(page.get("text", ""), query)
            results.append({
                "url": url,
                "title": page.get("title", url),
                "snippet": snippet,
                "image": page.get("image"),
                "score": score,
            })
        return results

    # fallback path (cosine on TF-IDF vectors)
    print("Semantic fallback (TF-IDF cosine) in use.")
    words = query.lower().split()
    if not words:
        return []

    counts = Counter(words)
    q_len = len(words)
    q_vec = {}
    for w, freq in counts.items():
        if w in idx.index:
            tf = freq / q_len
            df = len(idx.index[w])
            if df == 0:
                continue
            idf = math.log(N_DOCS / df)
            q_vec[w] = tf * idf

    def cosine(v1, v2):
        if not v1 or not v2:
            return 0.0
        dot = sum(v1[w] * v2.get(w, 0.0) for w in v1)
        n1 = math.sqrt(sum(x * x for x in v1.values()))
        n2 = math.sqrt(sum(x * x for x in v2.values()))
        if not n1 or not n2:
            return 0.0
        return dot / (n1 * n2)

    scores = []
    for url, dvec in doc_vectors.items():
        sim = cosine(q_vec, dvec)
        if sim > 0:
            scores.append((url, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    results = []
    for url, score in scores[:top_k]:
        page = docs.get(url, {})
        snippet = build_snippet(page.get("text", ""), query)
        results.append({
            "url": url,
            "title": page.get("title", url),
            "snippet": snippet,
            "image": page.get("image"),
            "score": float(score),
        })
    return results


# build semantic / fallback vectors at startup
build_semantic_embeddings()

# ---------------------
# Query tracking
# ---------------------
@app.after_request
def track_queries(response):
    query = request.args.get("q", "").strip()
    if query:
        trending_storage[query] = trending_storage.get(query, 0) + 1

        user = get_user_id()
        user_history[user] = user_history.get(user, []) + [query]

        if redis_enabled:
            try:
                r.zincrby("trending_searches", 1, query)
                r.zincrby(f"user:{user}:history", 1, query)
            except Exception:
                # silent fallback
                pass
    return response


# ---------------------
# ROUTES
# ---------------------
@app.get("/")
def home():
    return {"message": "Mini Search Engine with Semantic Search 🚀"}


@app.get("/search")
def perform_search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip().lower()

    filtered_docs = docs
    if category:
        filtered_docs = {
            url: data
            for url, data in docs.items()
            if data.get("category", "").lower() == category
        }

    total = max(len(filtered_docs), 1)
    results = search(query, idx, filtered_docs, total_docs=total)
    return jsonify(results[:50])


@app.get("/search_semantic")
def perform_search_semantic_route():
    query = request.args.get("q", "").strip()
    results = semantic_search(query, top_k=50)
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
    user = get_user_id()
    history = user_history.get(user, [])
    seen = set()
    unique_recent = []
    for q in reversed(history):
        if q not in seen:
            seen.add(q)
            unique_recent.append(q)
        if len(unique_recent) == 5:
            break
    return jsonify(list(reversed(unique_recent)))


@app.get("/user_history")
def get_user_history():
    user = get_user_id()
    return jsonify(user_history.get(user, []))


if __name__ == "__main__":
    app.run(debug=True)
