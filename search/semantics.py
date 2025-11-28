from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticSearch:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = {}  # url -> vector

    def build_embeddings(self, docs):
        for url, data in docs.items():
            text = data["text"]
            self.embeddings[url] = self.model.encode(text)

    def search(self, query, top_k=10):
        q_vec = self.model.encode(query).reshape(1, -1)
        scores = []

        for url, vec in self.embeddings.items():
            sim = cosine_similarity(q_vec, vec.reshape(1, -1))[0][0]
            scores.append((url, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
