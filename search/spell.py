# search/spell.py
import math

class Speller:
    def __init__(self, vocabulary):
        self.vocab = set(vocabulary)

    def edits1(self, word):
        letters = "abcdefghijklmnopqrstuvwxyz"
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts  = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def candidates(self, word):
        if word in self.vocab:
            return [word]
        edits = self.edits1(word)
        return [w for w in edits if w in self.vocab]

    def correct_query(self, query):
        words = query.lower().split()
        corrected = []
        changed = False

        for w in words:
            if w in self.vocab:
                corrected.append(w)
                continue
            cands = self.candidates(w)
            if cands:
                corrected.append(cands[0])  # first candidate
                changed = True
            else:
                corrected.append(w)

        return " ".join(corrected), changed
