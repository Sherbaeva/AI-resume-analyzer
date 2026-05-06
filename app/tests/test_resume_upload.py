"""Test: POST /resumes — upload, deduplication, size validation."""
import io
import pytest


@pytest.mark.asyncio
async def test_resume_upload_txt(admin_client, sample_txt_bytes):
    response = await admin_client.post(
        "/resumes",
        files={"file": ("my_resume.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "my_resume.txt"
    assert data["content_type"] == "text/plain"
    assert data["file_size"] == len(sample_txt_bytes)
    assert data["deleted_at"] is None


@pytest.mark.asyncio
async def test_resume_upload_invalid_type(admin_client):
    response = await admin_client.post(
        "/resumes",
        files={"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_resume_upload_too_large(admin_client):
    big_bytes = b"x" * (11 * 1024 * 1024)  # 11 MB — over default 10 MB limit
    response = await admin_client.post(
        "/resumes",
        files={"file": ("large.txt", io.BytesIO(big_bytes), "text/plain")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_resume_upload_unauthenticated(client, sample_txt_bytes):
    """No token — should be 401."""
    response = await client.post(
        "/resumes",
        files={"file": ("cv.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resume_get(admin_client, sample_txt_bytes):
    upload_resp = await admin_client.post(
        "/resumes",
        files={"file": ("cv.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    resume_id = upload_resp.json()["id"]
    get_resp = await admin_client.get(f"/resumes/{resume_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == resume_id


@pytest.mark.asyncio
async def test_resume_list(admin_client, sample_txt_bytes):
    """GET /resumes should return a list."""
    resp = await admin_client.get("/resumes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_resume_soft_delete(admin_client, sample_txt_bytes):
    upload_resp = await admin_client.post(
        "/resumes",
        files={"file": ("del_me.txt", io.BytesIO(sample_txt_bytes + b"unique"), "text/plain")},
    )
    resume_id = upload_resp.json()["id"]
    del_resp = await admin_client.delete(f"/resumes/{resume_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_at"] is not None

    # Deleted resume should 404
    get_resp = await admin_client.get(f"/resumes/{resume_id}")
    assert get_resp.status_code == 404
