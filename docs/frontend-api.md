# ATS API — Frontend Reference (v2 with Auth)

Base URL: `http://localhost:8000` (dev) / `https://api.yourdomain.com` (prod)

Swagger UI: `http://localhost:8000/docs`

---

## Authentication

All endpoints except `GET /health` require a **Bearer token**.

```
Authorization: Bearer <access_token>
```

> ⚠️ **Login is now 2-step (OTP via email).** After correct credentials, a 6-digit code is sent to the user's email. The JWT token is only returned after OTP verification.

### Step 1 — POST /auth/login
Validates credentials and sends OTP to email. **Does NOT return a token.**

**Request:**
```json
{ "email": "admin@ats-system.com", "password": "admin1234" }
```
**Response `200`:**
```json
{ "status": "otp_sent", "message": "A verification code has been sent to your email address." }
```
**Error `400`:** Invalid email or password.

---

### Step 2 — POST /auth/verify-otp
Verify the OTP code. Returns the JWT access token.

**Request:**
```json
{ "email": "admin@ats-system.com", "code": "483920" }
```
**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```
**Error `400`:** Invalid or expired verification code (code expires after 5 minutes).

---

### GET /auth/me 🔒
Returns current user profile + effective permissions.

**Response `200`:**
```json
{
  "id": 1,
  "email": "admin@ats-system.com",
  "role": "admin",
  "is_active": true,
  "permissions": ["analysis.write", "jd.read", "jd.write", "logs.view", ...]
}
```

### POST /auth/logout 🔒
Stateless logout — discard the token on the client side. Returns `204`.

---

## RBAC — Roles & Permissions

| Role  | Default Permissions |
|-------|---------------------|
| admin | All 11 permissions |
| hr    | `jd.write`, `jd.read`, `resumes.read`, `resumes.write`, `analysis.write`, `results.read`, `taxonomy.read` |

Admin can grant HR additional permissions via `PUT /users/{id}/permissions`.

**All permission codes:**
`users.manage` · `resumes.read` · `resumes.write` · `resumes.delete` · `taxonomy.manage` · `taxonomy.read` · `logs.view` · `jd.write` · `jd.read` · `analysis.write` · `results.read`

---

## Users API (admin · `users.manage`)

### POST /users — Create user
```json
{ "email": "hr@company.com", "password": "pass123", "role": "hr" }
```
Response `201`: `UserOut`

### GET /users — List users
Query: `?skip=0&limit=100`

### GET /users/{id} — Get user

### PATCH /users/{id} — Update user
```json
{ "role": "admin", "is_active": false, "password": "newpass" }
```

### DELETE /users/{id} — Deactivate user (soft delete)
Response `204`

### GET /users/{id}/permissions — List user's custom permissions
Response: `PermissionOut[]`

### PUT /users/{id}/permissions — Replace user's custom permissions
```json
{ "permission_codes": ["taxonomy.manage", "logs.view"] }
```

---

## Job Descriptions (`jd.write` · `jd.read`)

### POST /job-descriptions 🔒 (`jd.write`)
```json
{ "title": "Senior Python Engineer", "raw_text": "5 years Python..." }
```
Response `201`: `JobDescriptionResponse`

### GET /job-descriptions 🔒 (`jd.read`)
Query: `?skip=0&limit=50`
Returns `JobDescriptionResponse[]`, newest first.

### GET /job-descriptions/{id} 🔒 (`jd.read`)

---

## Resumes (`resumes.write` · `resumes.read` · `resumes.delete`)

### POST /resumes 🔒 (`resumes.write`)
`multipart/form-data` with field `file`. Accepts PDF, DOCX, TXT.
Response `201`: `ResumeResponse`

### GET /resumes 🔒 (`resumes.read`)
Query: `?skip=0&limit=50`
Returns `ResumeResponse[]`, newest first. Excludes soft-deleted resumes.

### GET /resumes/{id} 🔒 (`resumes.read`)

### DELETE /resumes/{id} 🔒 (`resumes.delete`)
Soft delete — sets `deleted_at`. Returns `ResumeResponse`.

---

## Analyses (`analysis.write` · `results.read`)

### POST /analyses 🔒 (`analysis.write`)
```json
{ "resume_id": 1, "job_description_id": 1 }
```
Idempotent — same pair returns existing. Response `201`: `AnalysisResponse`

**Status values:** `queued` → `running` → `done` / `failed`

### GET /analyses/{id} 🔒 (`results.read`)

### GET /results?job_description_id={id} 🔒 (`results.read`)
Returns `AnalysisResponse[]` for a given JD.

---

## Skill Taxonomy

### GET /taxonomy/skills 🔒 (`taxonomy.read`)
Query: `?q=python&category=Backend&is_active=true&skip=0&limit=100`

### GET /taxonomy/skills/{id} 🔒 (`taxonomy.read`)

### POST /taxonomy/skills 🔒 (`taxonomy.manage` — admin)
```json
{ "name": "FastAPI", "category": "Backend", "aliases": ["fast-api"] }
```
Response `201`: `SkillOut`

### PATCH /taxonomy/skills/{id} 🔒 (`taxonomy.manage`)
```json
{ "category": "Python", "is_active": true }
```

### DELETE /taxonomy/skills/{id} 🔒 (`taxonomy.manage`)
Soft delete (`is_active=false`). Returns `204`.

---

## Audit Logs (admin · `logs.view`)

### GET /logs/audit 🔒
Query params:
- `action` — filter by action (partial match), e.g. `auth.login`
- `entity_type` — e.g. `user`, `resume`, `skill_taxonomy`
- `actor_user_id` — filter by user
- `date_from`, `date_to` — ISO datetime strings
- `limit` (max 500, default 50), `offset`

Sorted by `created_at DESC`.

**Response:**
```json
[{
  "id": 1,
  "actor_user_id": 1,
  "action": "auth.login.success",
  "entity_type": "user",
  "entity_id": 1,
  "meta_json": null,
  "ip": "172.20.0.1",
  "user_agent": "curl/8.x",
  "created_at": "2026-02-24T10:00:00Z"
}]
```

---

## Error Format

All errors follow:
```json
{ "detail": "Error message" }
```
Or for validation errors:
```json
{
  "detail": [{ "loc": ["body", "email"], "msg": "...", "type": "..." }]
}
```

| Status | Meaning |
|--------|---------|
| `400`  | Invalid email or password (during login) |
| `401`  | Not authenticated / bad/expired token |
| `403`  | Authenticated but missing permission |
| `404`  | Resource not found |
| `409`  | Conflict (duplicate email, skill name, etc.) |
| `422`  | Validation error |

---

## TypeScript SDK Quick Start

```typescript
import { AtsClient, persistToken, clearToken } from "@/sdk/client";

const api = new AtsClient("http://localhost:8000");

// Login
const { access_token } = await api.login("admin@ats-system.com", "admin1234");
persistToken(access_token); // saves to localStorage

// Use
const me = await api.me();
const results = await api.getResults(jdId);
const skills = await api.listSkills({ q: "python", category: "Backend" });

// Logout
await api.logout();
clearToken();
```

---

## Internal Endpoint (n8n only, no JWT)

### POST /api/internal/analysis-callback
Used by n8n webhook. **Not for frontend.** Requires `X-N8N-SECRET` header.
