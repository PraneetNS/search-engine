# search/semantic.py
import numpy as np
from sentence_transformers import SentenceTransformer, util

class SemanticSearch:
    def __init__(self, docs):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.doc_ids = list(docs.keys())
        self.texts = [docs[id]["text"] for id in self.doc_ids]
        self.embeddings = self.model.encode(self.texts, convert_to_tensor=True)

    def search(self, query, top_k=10):
        q_emb = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(q_emb, self.embeddings, top_k=top_k)[0]
        results = []
        for h in hits:
            doc_id = self.doc_ids[h["corpus_id"]]
            score = float(h["score"])
            results.append((doc_id, score))
        return results
