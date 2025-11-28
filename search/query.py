import math

def search(query, idx, total_docs):
    query_words = query.lower().split()
    scores = {}

    for word in query_words:
        if word in idx.index:
            for doc_id in idx.index[word].keys():
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += idx.tfidf(word, doc_id, total_docs)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
