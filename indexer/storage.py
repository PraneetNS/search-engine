import json

def save_index(index, doc_lengths, filepath="data/index.json"):
    data = {
        "index": index,
        "doc_lengths": doc_lengths
    }
    with open(filepath, "w") as f:
        json.dump(data, f)

def load_index(filepath="data/index.json"):
    with open(filepath, "r") as f:
        data = json.load(f)
    return data["index"], data["doc_lengths"]
def save_index(index, doc_lengths, filepath="data/index.json"):
    data = {
        "index": index,
        "doc_lengths": doc_lengths
    }
    with open(filepath, "w") as f:
        json.dump(data, f)