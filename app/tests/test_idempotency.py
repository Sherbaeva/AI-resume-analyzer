"""Test: POST /analyses idempotency — same resume+jd returns same analysis."""
import io
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_analysis_idempotency(admin_client):
    resume_resp = await admin_client.post(
        "/resumes",
        files={"file": ("idempotency.txt", io.BytesIO(b"idempotency test resume xyz"), "text/plain")},
    )
    jd_resp = await admin_client.post(
        "/job-descriptions",
        json={"title": "Idempotency JD", "raw_text": "Test idempotency scenario."},
    )
    resume_id = resume_resp.json()["id"]
    jd_id = jd_resp.json()["id"]

    with patch("app.services.n8n_service.N8nService.trigger_analysis", new_callable=AsyncMock):
        resp1 = await admin_client.post(
            "/analyses",
            json={"resume_id": resume_id, "job_description_id": jd_id},
        )
        resp2 = await admin_client.post(
            "/analyses",
            json={"resume_id": resume_id, "job_description_id": jd_id},
        )

    assert resp1.status_code == 201
    assert resp2.status_code == 201
    # Same analysis returned (idempotent)
    assert resp1.json()["id"] == resp2.json()["id"]
