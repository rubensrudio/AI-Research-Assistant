import os
import time
import pytest
from httpx import Client
from uuid import uuid4  # <-- add

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@pytest.fixture()
def client():
    return Client(base_url=BASE_URL)

def _auth_headers(client: Client) -> dict:
    # unique email every run
    email = f"ragtest-{uuid4().hex}@local.com"
    r = client.post("/auth/register", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_rag_index_and_search(client: Client, tmp_path):
    headers = _auth_headers(client)

    # create project
    r = client.post("/projects", json={"name": "rag project", "description": "desc"}, headers=headers)
    assert r.status_code == 200, r.text
    project_id = r.json()["id"]

    # upload txt
    content = (
        "This is a test document about vector databases.\n"
        "Qdrant is a vector database used for similarity search.\n"
        "RAG combines retrieval with generation.\n"
    ) * 20
    p = tmp_path / "doc1.txt"
    p.write_text(content, encoding="utf-8")

    with open(p, "rb") as f:
        r = client.post(
            f"/projects/{project_id}/documents",
            files={"file": ("doc1.txt", f, "text/plain")},
            headers=headers,
        )
    assert r.status_code == 200, r.text

    # index
    r = client.post(f"/projects/{project_id}/rag/index", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["indexed"] >= 1

    # search (LM Studio pode demorar um pouco)
    time.sleep(0.5)
    r = client.post(
        f"/projects/{project_id}/rag/search",
        json={"query": "What is Qdrant used for?", "top_k": 5},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert len(results) >= 1
    assert any("Qdrant" in item["text"] for item in results)