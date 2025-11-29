import math


def build_snippet(text, query, window=160):
    if not text:
        return ""

    query = query.lower()
    clean_text = text.replace("\n", " ")

    idx = clean_text.lower().find(query)
    if idx == -1:
        return clean_text[:window] + "..."

    start = max(0, idx - window // 2)
    end = min(len(clean_text), idx + window // 2)
    snippet = clean_text[start:end]

    return ("..." + snippet + "...").strip()


def search(query, idx, docs, total_docs):
    query = query.strip().lower()
    if not query:
        return []  # do not return everything when search box empty!

    query_words = query.split()
    scores = {}

    # Compute TF-IDF relevance
    for word in query_words:
        if word in idx.index:
            for doc_id in idx.index[word].keys():
                scores[doc_id] = scores.get(doc_id, 0) + idx.tfidf(word, doc_id, total_docs)

    # Sort by relevance score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for doc_id, score in ranked:
        doc = docs.get(doc_id, {})
        snippet = build_snippet(doc.get("text", ""), query)

        results.append({
            "url": doc_id,
            "title": doc.get("title", doc_id),
            "snippet": snippet,
            "image": doc.get("image"),
            "score": float(score)
        })

    return results
