from collections import defaultdict
import math

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(dict)  # word -> {doc: freq}
        self.doc_lengths = {}

    def add_document(self, doc_id, text):
        words = text.lower().split()
        self.doc_lengths[doc_id] = len(words)

        for word in words:
            if doc_id not in self.index[word]:
                self.index[word][doc_id] = 0
            self.index[word][doc_id] += 1

    def tfidf(self, word, doc_id, total_docs):
        tf = self.index[word][doc_id] / self.doc_lengths[doc_id]
        df = len(self.index[word])
        idf = math.log(total_docs / df)
        return tf * idf
