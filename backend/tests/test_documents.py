"""
Tests for document endpoints.
"""
import io


def test_upload_txt_document(client, auth_headers):
    file_content = b"This is a test document about artificial intelligence."
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "pending"


def test_upload_unsupported_file_type(client, auth_headers):
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_requires_auth(client):
    file_content = b"Test document."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 401


def test_list_documents_empty(client, auth_headers):
    response = client.get("/api/v1/documents/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_after_upload(client, auth_headers):
    client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(b"Hello world."), "text/plain")},
    )
    response = client.get("/api/v1/documents/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_documents_requires_auth(client):
    response = client.get("/api/v1/documents/")
    assert response.status_code == 401


def test_delete_document(client, auth_headers):
    # Upload first
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(b"Hello world."), "text/plain")},
    )
    doc_id = upload.json()["id"]

    # Delete it
    response = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    list_response = client.get("/api/v1/documents/", headers=auth_headers)
    assert list_response.json() == []


def test_delete_nonexistent_document(client, auth_headers):
    response = client.delete(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404