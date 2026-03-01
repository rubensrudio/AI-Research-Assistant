import os
import pytest
from httpx import Client

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@pytest.fixture()
def client():
    return Client(base_url=BASE_URL)

def test_health(client: Client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_auth_projects_and_upload(client: Client, tmp_path):
    # register
    r = client.post("/auth/register", json={"email": "pytest@local.com", "password": "Password123!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create project
    r = client.post("/projects", json={"name": "pytest project", "description": "desc"}, headers=headers)
    assert r.status_code == 200
    project_id = r.json()["id"]

    # upload file
    p = tmp_path / "a.txt"
    p.write_text("hello world")
    with open(p, "rb") as f:
        r = client.post(f"/projects/{project_id}/documents", files={"file": ("a.txt", f, "text/plain")}, headers=headers)
    assert r.status_code == 200
    assert r.json()["filename"] == "a.txt"

    # list docs
    r = client.get(f"/projects/{project_id}/documents", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1