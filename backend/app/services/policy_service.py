import io
import re

import faiss
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session

from app import models

MAX_CHARS = 450          # longest passage stored
MIN_CHARS = 40           # shorter passages (headers, page numbers) are skipped
MAX_BYTES = 10 * 1024 * 1024

_vectorizer = None
_index = None
_chunks = []
_dirty = True


def pdf_to_passages(data: bytes) -> tuple[int, list]:
    """Read a PDF and split each page into passages of whole sentences."""
    reader = PdfReader(io.BytesIO(data))
    passages = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        current = ""
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            while len(sentence) > MAX_CHARS:
                passages.append((page_no, sentence[:MAX_CHARS]))
                sentence = sentence[MAX_CHARS:]
            if current and len(current) + len(sentence) + 1 > MAX_CHARS:
                passages.append((page_no, current))
                current = ""
            current = f"{current} {sentence}".strip()
        if current:
            passages.append((page_no, current))
    return len(reader.pages), [(p, t) for p, t in passages if len(t) >= MIN_CHARS]


def mark_dirty():
    global _dirty
    _dirty = True


def _build(db: Session):
    global _vectorizer, _index, _chunks, _dirty
    rows = db.query(models.PolicyChunk).order_by(models.PolicyChunk.id).all()
    _chunks = [{"document": r.document_name, "page": r.page, "text": r.text} for r in rows]
    _vectorizer, _index = None, None
    if _chunks:
        _vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = _vectorizer.fit_transform([c["text"] for c in _chunks]).toarray().astype("float32")
        faiss.normalize_L2(matrix)
        _index = faiss.IndexFlatIP(matrix.shape[1])
        _index.add(matrix)
    _dirty = False


def search_policies(db: Session, query: str, k: int = 3, min_score: float = 0.1) -> list:
    if _dirty:
        _build(db)
    if _index is None:
        return []
    query_vector = _vectorizer.transform([query]).toarray().astype("float32")
    faiss.normalize_L2(query_vector)
    scores, ids = _index.search(query_vector, min(k, len(_chunks)))
    return [_chunks[i] for s, i in zip(scores[0], ids[0]) if i >= 0 and s >= min_score]