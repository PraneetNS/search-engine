import json

def save_index(index, doc_lengths, docs):
    with open("data/index.json", "w", encoding="utf-8") as f:
        json.dump({"index": index, "doc_lengths": doc_lengths, "docs": docs}, f)

def load_index():
    with open("data/index.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["index"], data["doc_lengths"], data["docs"]
