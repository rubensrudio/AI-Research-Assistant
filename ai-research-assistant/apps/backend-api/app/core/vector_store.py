from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(host="localhost", port=6333)

def create_collection():
    client.recreate_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    
    # client.upsert(
    #     collection_name="documents",
    #     points=[
    #         {
    #             "id": 1,
    #             "vector": [0.1]*1536,
    #             "payload": {"project_id": 1, "text": "sample text"}
    #         }
    #     ]
    # )