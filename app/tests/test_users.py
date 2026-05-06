"""Tests for Users CRUD (admin only) and permission management."""
import pytest


@pytest.mark.asyncio
async def test_admin_can_create_user(admin_client):
    resp = await admin_client.post("/users", json={
        "email": "newhr@test.local",
        "password": "password123",
        "role": "hr",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newhr@test.local"
    assert data["role"] == "hr"


@pytest.mark.asyncio
async def test_hr_cannot_create_user(hr_client):
    resp = await hr_client.post("/users", json={
        "email": "another@test.local",
        "password": "password123",
        "role": "hr",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users(admin_client):
    resp = await admin_client.get("/users")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_admin_deactivate_user(admin_client, hr_user):
    resp = await admin_client.delete(f"/users/{hr_user['id']}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_set_permissions(admin_client, hr_user):
    resp = await admin_client.put(
        f"/users/{hr_user['id']}/permissions",
        json={"permission_codes": ["taxonomy.manage", "logs.view"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["permissions"]) >= {"taxonomy.manage", "logs.view"}


@pytest.mark.asyncio
async def test_duplicate_email_rejected(admin_client, hr_user):
    resp = await admin_client.post("/users", json={
        "email": hr_user["email"],
        "password": "password123",
        "role": "hr",
    })
    assert resp.status_code == 409
