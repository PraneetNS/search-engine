import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from crawler.crawler import Crawler
from indexer.inverted_index import InvertedIndex
from search.query import search
from indexer.storage import save_index, load_index
from search.autocomplete import Trie
from search.semantics import SemanticSearch

app = Flask(__name__)
CORS(app)


# ---------------------
# LOAD OR BUILD INDEX
# ---------------------

idx = InvertedIndex()
docs = {}
print("DOCS COUNT:", len(docs))
print("FIRST DOCS:", list(docs.keys())[:3])
semantic = SemanticSearch()
semantic.build_embeddings(docs)
print("Semantic embeddings built for", len(semantic.embeddings), "docs")

try:
    index_data, doc_lengths, stored_docs = load_index()
    idx.index = index_data
    idx.doc_lengths = doc_lengths
    docs = stored_docs
    print("Loaded index & docs from storage.")
except:
    print("Index not found — crawling now...")
    crawler = Crawler(max_pages=50)
    docs = crawler.crawl("https://en.wikipedia.org/wiki/India")

    for url, data in docs.items():
        idx.add_document(url, data["text"])

    save_index(idx.index, idx.doc_lengths, docs)
    print("Index & docs saved.")


# ---------------------
# BUILD AUTOCOMPLETE TRIE
# ---------------------

trie = Trie()
for word in idx.index.keys():
    trie.insert(word)
print("Trie loaded with", len(idx.index), "words.")

# ---------------------
# ROUTES
# ---------------------

@app.get("/")
def home():
    return {"message": "Mini Search Engine running. Try /search?q=text or /suggest?q=pre"}

@app.get("/search")
def perform_search():
    query = request.args.get("q", "")
    results = search(query, idx, total_docs=len(idx.doc_lengths))

    formatted = []
    for url, score in results[:10]:
        doc = docs.get(url, {})
        formatted.append({
            "url": url,
            "title": doc.get("title", url),
            "snippet": doc.get("text", "")[:250] + "...",
            "image": doc.get("image"),
            "score": score,
        })

    print("QUERY:", query)
    print("RESULTS:", formatted[:2])  # quick debug
    return jsonify(formatted)




@app.get("/suggest")
def suggest():
    prefix = request.args.get("q", "")
    suggestions = trie.autocomplete(prefix)
    return jsonify(suggestions[:10])
@app.get("/search_semantic")
def search_semantic():
    query = request.args.get("q", "")
    results = semantic.search(query, top_k=10)

    formatted = []
    for url, score in results:
        doc = docs.get(url, {})
        formatted.append({
            "url": url,
            "title": doc.get("title", url),
            "snippet": doc.get("text", "")[:250] + "...",
            "score": score,
        })

    return jsonify(formatted)


if __name__ == "__main__":
    app.run(debug=True)
