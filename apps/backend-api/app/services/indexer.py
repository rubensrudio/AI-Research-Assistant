from __future__ import annotations
from pathlib import Path

from qdrant_client.models import PointStruct

from app.services.lmstudio_client import embed_text
from app.services.chunking import chunk_text
from app.services.qdrant_store import ensure_collection, upsert_chunks


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Document path is not a file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def index_document(
    project_id: int,
    doc_id: int,
    filename: str,
    storage_path: str,
    chunk_max_chars: int = 1200,
    chunk_overlap: int = 200,
) -> dict:
    path = Path(storage_path)
    text = read_text_file(path)

    chunks = chunk_text(text, max_chars=chunk_max_chars, overlap=chunk_overlap)
    if not chunks:
        return {"doc_id": doc_id, "chunks": 0, "dim": 0, "error": "Document is empty after chunking"}

    probe_vec = embed_text([chunks[0]])[0]
    dim = len(probe_vec)

    ensure_collection(project_id, vector_size=dim)

    vectors = embed_text(chunks)

    points: list[PointStruct] = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        pid = doc_id * 1_000_000 + i

        payload = {
            "project_id": project_id,
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}-{i}",
            "text": chunk,
            "filename": filename,
            "storage_path": storage_path,
        }
        points.append(PointStruct(id=pid, vector=vec, payload=payload))

    upsert_chunks(project_id, points)

    return {"doc_id": doc_id, "chunks": len(points), "dim": dim}