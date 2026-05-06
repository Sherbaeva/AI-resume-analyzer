# ATS Backend 2.0 API Guide 🤖

> **Target Audience:** AI Assistant / Frontend Developer
> **Goal:** Integrate a Vue/React frontend with the ATS Backend. All endpoints use JWT `Bearer` token auth and expect JSON payloads.

---

## 1. Authentication Flow

The backend uses stateless JWT Bearer tokens with an expiration time of 60 mins.

- **Storage:** Frontend MUST store the `access_token` in `localStorage` or memory. Do NOT use cookies.
- **Header:** Include `Authorization: Bearer <access_token>` on all requests except `/auth/login` and `/health`.
- **RBAC:** Roles determine permissions. The `admin` role has full access. The `hr` role has limited access. Additional permissions can be injected manually for `hr` users.
- **Handling token expiration:** If a request returns `401 Unauthorized`, the token has expired. The user MUST be redirected to the login screen.
- **Login is 2-step (OTP 2FA):** Correct credentials trigger an OTP email. JWT is only returned after OTP verification.

### Endpoints
* **`POST /auth/login`**
  * Payload: `{"email": "admin@ats-system.com", "password": "..."}`
  * Response: `{"status": "otp_sent", "message": "..."}`  ← **No token yet!**
  * Error `400`: invalid credentials
* **`POST /auth/verify-otp`**
  * Payload: `{"email": "admin@ats-system.com", "code": "483920"}`
  * Response: `{"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}`
  * Error `400`: invalid or expired code (expires after 5 minutes)
* **`GET /auth/me`** (Requires `Bearer` token)
  * Returns the current authenticated user profile, their assigned `role`, and flat list of raw `permissions` (`[ "analysis.write", "jd.read" ]`). Use this array to implement frontend RBAC guards.
  * Response: `{"id": 1, "email": "...", "role": "admin", "is_active": true, "permissions": ["users.manage", ...]}`

---

## 2. Core Entities

### Job Descriptions (`/job-descriptions`)

* **Create a Job Description:** `POST /job-descriptions`
  * Requires Permission: `jd.write`
  * Payload: `{"title": "Backend Dev", "raw_text": "Python, SQL"}`
  * Response: `{"id": 1, "title": "Backend Dev", "raw_text": "Python, SQL", "created_at": "..."}`
* **Get Job Descriptions:** `GET /job-descriptions`
  * Requires Permission: `jd.read`
  * Response: Array of Job Description objects.
* **Get Job Description by ID:** `GET /job-descriptions/{id}`
  * Requires Permission: `jd.read`
  * Response: Single Job Description object.

### Resumes (`/resumes`)

* **Upload a Resume:** `POST /resumes` **(multipart/form-data)**
  * Requires Permission: `resumes.write`
  * File types allowed: `pdf`, `docx`, `txt`. Max size default: 10MB.
  * Body: `file` attribute containing the raw file payload.
  * Response: `{"id": 1, "file_path": "storage/...pdf", "file_hash": "...", "size_bytes": 1024, "created_at": "..."}`
* **Get Resumes:** `GET /resumes`
  * Requires Permission: `resumes.read`
  * Params (Optional): `job_description_id` query param.
  * Response: Array of Resume objects.
* **Get Resume Download Stream:** `GET /resumes/{id}/download`
  * Requires Permission: `resumes.read`
  * Response: Raw file content stream.
* **Soft Delete Resume:** `DELETE /resumes/{id}`
  * Requires Permission: `resumes.delete`
  * Response: `{"id": 1, ... "deleted_at": "2024-..."}`

### Analysis & Results (`/analyses` and `/results`)

The analysis process is asynchronous and idempotent.

* **Trigger Analysis:** `POST /analyses`
  * Requires Permission: `analysis.write`
  * Payload: `{"resume_id": 1, "job_description_id": 1}`
  * Response: `{"id": 1, "resume_id": 1, "job_description_id": 1, "status": "queued", ...}`
  * *Note:* If the same JD + Resume combo is submitted again, the existing `analysis_id` is returned.
* **Poll Status:** `GET /analyses/{id}`
  * Requires Permission: `results.read`
  * The frontend MUST poll this endpoint until `status` is either `"done"` or `"failed"`.
  * Response when done:
    ```json
    {
      "id": 1,
      "status": "done",
      "score": 85.5,
      "matched_skills_json": "[\"Python\", \"SQL\"]",
      "missing_skills_json": "[\"AWS\"]",
      "explanations_json": "{\"summary\": \"Great developer.\"}"
    }
    ```
    *⚠️ CRITICAL NOTE:* The skills and explanations fields end in `_json` and their values are **STRINGS**. The frontend must `JSON.parse()` these fields. Do not treat them as direct arrays/objects.
* **Get Results for a JD:** `GET /results?job_description_id={id}`
  * Requires Permission: `results.read`
  * Useful for rendering a dashboard of scores.

---

## 3. Administration (Mostly `admin` role)

### Users (`/users`)
*Requires `users.manage` permission.*

* **Get Users:** `GET /users`
* **Create User:** `POST /users` -> Payload: `{"email": "", "password": "", "role": "hr", "is_active": true}`
* **Update User:** `PATCH /users/{id}`
* **Soft Delete User:** `DELETE /users/{id}`

### Role & Permissions (`/users/{id}/permissions`)
*Requires `users.manage` permission.*

* **Get Permissions for User:** `GET /users/{id}/permissions`
  * Response: `["resumes.write", "jd.read"]`
* **Set Permissions for User:** `PUT /users/{id}/permissions`
  * Payload: `{"permission_codes": ["resumes.write", "jd.read"]}`. Replaces all existing manually-granted permissions.

### Taxonomy (Skills Management)
*Requires `taxonomy.read` for reading, `taxonomy.manage` for writing.*

* **List Skills:** `GET /taxonomy/skills`
  * Params (Optional): `q=search_string`, `category=Backend`, `is_active=true`
* **Create Skill:** `POST /taxonomy/skills`  -> Payload: `{"name": "Python", "category": "Backend"}`
* **Update Skill:** `PATCH /taxonomy/skills/{id}`
* **Delete Skill:** `DELETE /taxonomy/skills/{id}`

### Audit Logs
*Requires `logs.view` permission.*

* **View Logs:** `GET /logs/audit`
  * Params (Optional): `limit`, `offset`, `action`, `entity_type`, `actor_user_id`

---

## 4. Frontend SDK Integration Quick Start

A ready-to-use TypeScript SDK has been generated alongside the backend.

1. Locate the `types.ts` and `client.ts` files (likely provided by the developer in `sdk/ts/`).
2. Copy them into your frontend project at `src/api/`.
3. Use the `AtsClient` class to make typed requests, handling token persistence via the provided helpers.

```typescript
// Example Implementation
import { AtsClient, persistToken } from '@/api/client';

const api = new AtsClient(import.meta.env.VITE_API_BASE_URL);

// 1. Auth Flow
const authResponse = await api.login('admin@ats-system.com', 'admin1234');
persistToken(authResponse.access_token);
const profile = await api.me(); // Can be stored in Vuex/Pinia/Zustand

// 2. Upload + Analyze Flow
const jd = await api.createJobDescription({ title: "Dev", raw_text: "..." });
const resume = await api.uploadResume(fileObject); // File object from input[type="file"]
let analysis = await api.createAnalysis({ resume_id: resume.id, job_description_id: jd.id });

// 3. Polling Example
const interval = setInterval(async () => {
    analysis = await api.getAnalysis(analysis.id);
    if (['done', 'failed'].includes(analysis.status)) {
        clearInterval(interval);
        if (analysis.status === 'done') {
             const matched = JSON.parse(analysis.matched_skills_json ?? '[]');
             console.log("Score:", analysis.score, "Matched:", matched);
        }
    }
}, 3000);
```

### Important HTTP Error Codes to Handle
- **`400`**: Invalid email or password during login.
- **`422`**: Validation errors (check `response.data.detail`).
- **`401`**: Authentication failure (missing token or token expired). Must clear localStorage and redirect to `/login`.
- **`403`**: Authorization failure (user lacks required permission string like `resumes.delete` for the action). Inform user they don't have access. Do not redirect them.
- **`404`**: Resource not found.
- **`409`**: Conflict (e.g., trying to create a user email that already exists).
