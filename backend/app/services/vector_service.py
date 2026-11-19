from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[3]
df = pd.read_csv(ROOT / "data" / "sample_risks.csv")

vectorizer = None
index = None


def build_index():
    global vectorizer, index
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(df["description"]).toarray().astype("float32")
    faiss.normalize_L2(matrix)
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)


def search_similar(query: str, k: int = 3) -> list:
    if index is None:
        build_index()
    query_vector = vectorizer.transform([query]).toarray().astype("float32")
    faiss.normalize_L2(query_vector)
    _, ids = index.search(query_vector, k)
    return df.iloc[ids[0]].to_dict(orient="records")