"""Tests for RBAC permission checks on taxonomy endpoints."""
import pytest


@pytest.mark.asyncio
async def test_hr_can_read_taxonomy(hr_client):
    resp = await hr_client.get("/taxonomy/skills")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_hr_cannot_create_taxonomy(hr_client):
    resp = await hr_client.post("/taxonomy/skills", json={
        "name": "Kubernetes",
        "category": "DevOps",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_taxonomy(admin_client):
    resp = await admin_client.post("/taxonomy/skills", json={
        "name": "FastAPI",
        "category": "Backend",
        "aliases": ["fast-api"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "FastAPI"


@pytest.mark.asyncio
async def test_unauthenticated_taxonomy_blocked(client):
    resp = await client.get("/taxonomy/skills")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_hr_with_extra_permission_can_create(hr_client, hr_user, admin_client):
    """After granting taxonomy.manage to hr, they can create skills."""
    await admin_client.put(
        f"/users/{hr_user['id']}/permissions",
        json={"permission_codes": ["taxonomy.manage"]},
    )
    resp = await hr_client.post("/taxonomy/skills", json={
        "name": "PostgreSQL",
        "category": "Database",
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_unauthenticated_resumes_blocked(client):
    resp = await client.get("/resumes/1")
    assert resp.status_code == 401
