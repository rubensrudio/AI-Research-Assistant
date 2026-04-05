from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import settings


@dataclass(frozen=True)
class RetrievedChunk:
    score: float
    doc_id: int
    chunk_id: str
    text: str
    filename: str
    storage_path: str


_client: QdrantClient | None = None


def _qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def collection_name(project_id: int) -> str:
    return f"proj_{project_id}_docs"


def ensure_collection(project_id: int, vector_size: int):
    client = _qdrant_client()
    name = collection_name(project_id)

    existing = {c.name for c in client.get_collections().collections}
    if name in existing:
        return

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upsert_chunks(project_id: int, points: list[PointStruct]):
    client = _qdrant_client()
    name = collection_name(project_id)
    client.upsert(collection_name=name, points=points)


def search(project_id: int, query_vector: list[float], top_k: int = 5, doc_id: int | None = None) -> list[RetrievedChunk]:
    client = _qdrant_client()
    name = collection_name(project_id)

    qfilter = None
    if doc_id is not None:
        qfilter = Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )

    res = client.search(
        collection_name=name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qfilter,
        with_payload=True,
    )

    out: list[RetrievedChunk] = []
    for r in res:
        payload = r.payload or {}
        out.append(
            RetrievedChunk(
                score=float(r.score),
                doc_id=int(payload.get("doc_id", -1)),
                chunk_id=str(payload.get("chunk_id", "")),
                text=str(payload.get("text", "")),
                filename=str(payload.get("filename", "")),
                storage_path=str(payload.get("storage_path", "")),
            )
        )
    return out