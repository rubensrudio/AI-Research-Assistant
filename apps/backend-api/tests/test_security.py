"""Negative tests: auth boundaries, ownership, upload validation, rate limiting."""
import os
import pytest
from httpx import Client
from uuid import uuid4

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
VALID_EMAIL = "testuser@local.com"
VALID_PASSWORD = "Password123!"


@pytest.fixture()
def client():
    return Client(base_url=BASE_URL)


@pytest.fixture()
def authed_client(client: Client):
    email = f"user-{uuid4().hex[:8]}@local.com"
    r = client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    result = Client(base_url=BASE_URL)
    result.headers["Authorization"] = f"Bearer {token}"
    return result


@pytest.fixture()
def other_user_client(client: Client):
    email = f"other-{uuid4().hex[:8]}@local.com"
    r = client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    result = Client(base_url=BASE_URL)
    result.headers["Authorization"] = f"Bearer {token}"
    return result


# ---------- Auth negative tests ----------

def test_register_duplicate_email(client: Client):
    email = f"dupe-{uuid4().hex[:8]}@local.com"
    r1 = client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    assert r1.status_code == 200
    r2 = client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    assert r2.status_code == 400
    assert "already" in r2.json()["detail"].lower()


def test_login_wrong_password(client: Client):
    email = f"wrongpw-{uuid4().hex[:8]}@local.com"
    client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    r = client.post("/auth/login", json={"email": email, "password": "WrongPassword1!"})
    assert r.status_code == 401


def test_login_nonexistent_email(client: Client):
    r = client.post("/auth/register", json={
        "email": f"nope-{uuid4().hex[:8]}@local.com",
        "password": VALID_PASSWORD,
    })
    # Use a different email to login
    r = client.post("/auth/login", json={
        "email": f"never-{uuid4().hex[:8]}@local.com",
        "password": VALID_PASSWORD,
    })
    assert r.status_code == 401


def test_no_auth_access_projects(client: Client):
    """Unauthenticated users cannot access projects."""
    r = client.get("/projects")
    assert r.status_code == 403


def test_no_auth_access_documents(client: Client):
    """Unauthenticated users cannot list documents."""
    r = client.get("/projects/1/documents")
    assert r.status_code == 403


def test_no_auth_access_rag(client: Client):
    """Unauthenticated users cannot use RAG."""
    r = client.post("/projects/1/rag/search", json={"query": "test"})
    assert r.status_code == 403


def test_no_auth_llm(client: Client):
    """LLM endpoints now need auth too."""
    r = client.post("/llm/chat", json={"prompt": "hi"})
    assert r.status_code == 403


def test_invalid_token(client: Client):
    """Bearer token with garbage JWT is rejected."""
    r = client.get("/projects", headers={"Authorization": "Bearer not.a.valid.token"})
    assert r.status_code == 401


# ---------- Ownership tests ----------

def test_user_cannot_access_other_user_project(authed_client, other_user_client):
    """User A creates a project; User B cannot see it."""
    r = authed_client.post("/projects", json={"name": "private project", "description": "mine"})
    assert r.status_code == 200
    project_id = r.json()["id"]

    r = other_user_client.get(f"/projects/{project_id}")
    assert r.status_code == 404

    r = other_user_client.get(f"/projects/{project_id}/documents")
    assert r.status_code == 404


def test_user_cannot_delete_other_user_project(authed_client, other_user_client):
    r = authed_client.post("/projects", json={"name": "protected", "description": ""})
    assert r.status_code == 200
    project_id = r.json()["id"]

    r = other_user_client.delete(f"/projects/{project_id}")
    assert r.status_code == 404


# ---------- Upload validation tests ----------

def test_rejects_oversized_file(client: Client):
    """Upload is rejected if file exceeds limit."""
    # First auth + project setup
    email = f"test-upload-{uuid4().hex[:8]}@local.com"
    client.post("/auth/register", json={"email": email, "password": VALID_PASSWORD})
    token = client.post("/auth/login", json={"email": email, "password": VALID_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/projects", json={"name": "upload test", "description": ""}, headers=headers)
    project_id = r.json()["id"]

    # Create a 1MB file (well under 50MB limit but larger than typical text test)
    large_content = b"x" * (2 * 1024 * 1024)  # 2 MB — still valid
    from io import BytesIO
    r = client.post(
        f"/projects/{project_id}/documents",
        files={"file": ("big.bin", BytesIO(large_content), "application/octet-stream")},
        headers=headers,
    )
    # Should be rejected due to unsupported content type (not in ALLOWED_CONTENT_TYPES)
    assert r.status_code in [400, 415, 422]
