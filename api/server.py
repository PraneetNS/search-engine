import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from crawler.crawler import Crawler
from indexer.inverted_index import InvertedIndex
from search.query import search
from indexer.storage import save_index, load_index
save_index(idx.index, idx.doc_lengths)
try:
    index_data, doc_lengths = load_index()
    idx.index = index_data
    idx.doc_lengths = doc_lengths
    docs = None   # No need for docs list until needed
    print("Loaded index from file, skipping crawl.")
except:
    print("No saved index found, crawling now...")
    pages = crawler.crawl("https://en.wikipedia.org/wiki/India")

    for url, text in pages.items():
        idx.add_document(url, text)

    docs = pages
    save_index(idx.index, idx.doc_lengths)

app = Flask(__name__)

# ---- Crawl ONCE at startup ----
crawler = Crawler(max_pages=50)
pages = crawler.crawl("https://en.wikipedia.org/wiki/India")

print("CRAWLED PAGES:", len(pages))
for url, text in pages.items():
    print("URL:", url)
    print("TEXT SNIPPET:", text[:300])
    break  # Print only first page

print("PAGES LIST:", list(pages.keys())[:5])

# ---- Build index ----
idx = InvertedIndex()
for url, text in pages.items():
    print(url, "->", text[:200])


print("INDEX SIZE:", len(idx.index))
docs = pages


# ---- Home Route ----
@app.get("/")
def home():
    return {"message": "Mini Search Engine is running. Use /search?q=your_term"}


# ---- Search Route ----
@app.get("/search")
def perform_search():
    query = request.args.get("q")
    print("QUERY RECEIVED:", query)

    results = search(query, idx, total_docs=len(docs))
    print("RESULTS:", results)

    return jsonify({"query": query, "results": results[:10]})


if __name__ == "__main__":
    app.run(debug=True)
