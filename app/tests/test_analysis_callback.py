"""Test: POST /api/internal/analysis-callback — validates secret and updates analysis."""
import io
import pytest
from unittest.mock import AsyncMock, patch
from app.core.config import get_settings

settings = get_settings()


async def _setup_analysis(admin_client):
    resume_resp = await admin_client.post(
        "/resumes",
        files={"file": ("callback_test.txt", io.BytesIO(b"callback resume content abc"), "text/plain")},
    )
    jd_resp = await admin_client.post(
        "/job-descriptions",
        json={"title": "Callback Test JD", "raw_text": "Need Python and FastAPI."},
    )
    resume_id = resume_resp.json()["id"]
    jd_id = jd_resp.json()["id"]

    with patch("app.services.n8n_service.N8nService.trigger_analysis", new_callable=AsyncMock):
        analysis_resp = await admin_client.post(
            "/analyses",
            json={"resume_id": resume_id, "job_description_id": jd_id},
        )
    return analysis_resp.json()["id"]


@pytest.mark.asyncio
async def test_callback_done(admin_client):
    analysis_id = await _setup_analysis(admin_client)

    payload = {
        "analysis_id": analysis_id,
        "status": "done",
        "score": 87.5,
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": ["Kubernetes"],
        "explanations": {"summary": "Great match"},
    }
    resp = await admin_client.post(
        "/api/internal/analysis-callback",
        json=payload,
        headers={"X-N8N-SECRET": settings.N8N_SECRET},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["score"] == 87.5
    assert data["finished_at"] is not None


@pytest.mark.asyncio
async def test_callback_failed(admin_client):
    analysis_id = await _setup_analysis(admin_client)
    payload = {
        "analysis_id": analysis_id,
        "status": "failed",
        "error_message": "OpenAI timeout",
    }
    resp = await admin_client.post(
        "/api/internal/analysis-callback",
        json=payload,
        headers={"X-N8N-SECRET": settings.N8N_SECRET},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_callback_wrong_secret(admin_client):
    """Wrong secret should always return 403, regardless of auth."""
    payload = {"analysis_id": 1, "status": "done"}
    resp = await admin_client.post(
        "/api/internal/analysis-callback",
        json=payload,
        headers={"X-N8N-SECRET": "wrong_secret"},
    )
    assert resp.status_code == 403
