"""Test: POST /analyses — creates analysis, n8n mocked."""
import io
import pytest
from unittest.mock import AsyncMock, patch


async def _create_resume(client, content=b"FastAPI developer resume"):
    resp = await client.post(
        "/resumes",
        files={"file": ("cv.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_jd(client, title="Backend Engineer"):
    resp = await client.post(
        "/job-descriptions",
        json={"title": title, "raw_text": "We need FastAPI, PostgreSQL, Redis skills."},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_analysis(admin_client):
    resume_id = await _create_resume(admin_client)
    jd_id = await _create_jd(admin_client)

    with patch("app.services.n8n_service.N8nService.trigger_analysis", new_callable=AsyncMock):
        resp = await admin_client.post(
            "/analyses",
            json={"resume_id": resume_id, "job_description_id": jd_id},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["resume_id"] == resume_id
    assert data["job_description_id"] == jd_id
    assert data["status"] in ("processing", "failed", "queued")


@pytest.mark.asyncio
async def test_create_analysis_missing_resume(admin_client):
    jd_id = await _create_jd(admin_client, title="Missing Resume Test")
    resp = await admin_client.post(
        "/analyses",
        json={"resume_id": 99999, "job_description_id": jd_id},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_analysis(admin_client):
    resume_id = await _create_resume(admin_client, b"unique get analysis content")
    jd_id = await _create_jd(admin_client, "Get Analysis JD")

    with patch("app.services.n8n_service.N8nService.trigger_analysis", new_callable=AsyncMock):
        create_resp = await admin_client.post(
            "/analyses",
            json={"resume_id": resume_id, "job_description_id": jd_id},
        )
    analysis_id = create_resp.json()["id"]

    get_resp = await admin_client.get(f"/analyses/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == analysis_id
