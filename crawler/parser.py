import re

STOPWORDS = {"the","is","are","a","an","and","of","to","in","on","for","with","by","at","from","as","this","that"}

def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    words = text.split()
    return [w for w in words if w not in STOPWORDS]
