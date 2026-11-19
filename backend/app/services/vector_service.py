import os
import faiss
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "sample_risks.csv"
)

df = pd.read_csv(CSV_PATH)
index = None


def get_embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return np.array(response.data[0].embedding, dtype="float32")


def build_index():
    global index
    vectors = np.vstack([get_embedding(t) for t in df["description"]])
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)


def search_similar(query: str, k: int = 3) -> list:
    if index is None:
        build_index()
    query_vector = get_embedding(query).reshape(1, -1)
    _, ids = index.search(query_vector, k)
    return df.iloc[ids[0]].to_dict(orient="records")