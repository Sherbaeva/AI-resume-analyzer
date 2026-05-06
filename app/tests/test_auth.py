"""Tests for auth endpoints: login (OTP 2FA), verify-otp, me, logout."""
import pytest
from unittest.mock import AsyncMock, patch


# ─── Login Step 1 tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_sends_otp(client, admin_user):
    """Step 1: correct credentials should return otp_sent (not a token)."""
    with patch("app.auth.router.save_otp", new_callable=AsyncMock), \
         patch("app.auth.router.send_otp_email", new_callable=AsyncMock):
        resp = await client.post("/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "otp_sent"
    assert "access_token" not in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post("/auth/login", json={
        "email": admin_user["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "anything",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_email_smtp_failure_returns_503(client, admin_user):
    """If SMTP fails, login should return 503 and not leak the OTP."""
    with patch("app.auth.router.save_otp", new_callable=AsyncMock), \
         patch("app.auth.router.delete_otp", new_callable=AsyncMock), \
         patch("app.auth.router.send_otp_email",
               new_callable=AsyncMock, side_effect=Exception("SMTP error")):
        resp = await client.post("/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
    assert resp.status_code == 503


# ─── Login Step 2 (verify-otp) tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_otp_success(client, admin_user):
    """Step 2: valid OTP should return JWT token."""
    with patch("app.auth.router.verify_otp", new_callable=AsyncMock, return_value=True):
        resp = await client.post("/auth/verify-otp", json={
            "email": admin_user["email"],
            "code": "123456",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_verify_otp_invalid_code(client, admin_user):
    """Wrong or expired code should return 400."""
    with patch("app.auth.router.verify_otp", new_callable=AsyncMock, return_value=False):
        resp = await client.post("/auth/verify-otp", json={
            "email": admin_user["email"],
            "code": "000000",
        })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_otp_unknown_email(client):
    """OTP verify for non-existent email should return 400."""
    with patch("app.auth.router.verify_otp", new_callable=AsyncMock, return_value=False):
        resp = await client.post("/auth/verify-otp", json={
            "email": "ghost@example.com",
            "code": "123456",
        })
    assert resp.status_code == 400


# ─── /me and /logout ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_with_token(client, admin_token):
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"
    assert "users.manage" in data["permissions"]


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client, admin_token):
    resp = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204
