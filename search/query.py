def search(query, index, total_docs):
    terms = query.lower().split()
    scores = {}

    for term in terms:
        if term not in index.index:
            continue

        for doc_id in index.index[term]:
            score = index.tfidf(term, doc_id, total_docs)
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
