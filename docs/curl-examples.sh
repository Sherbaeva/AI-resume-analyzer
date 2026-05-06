#!/usr/bin/env bash
# ATS API — curl examples (v2 with Auth)
# Usage: TOKEN=$(./curl-examples.sh login | jq -r .access_token)
set -euo pipefail

BASE="${ATS_BASE_URL:-http://localhost:8000}"
EMAIL="${ATS_EMAIL:-admin@ats-system.com}"
PASSWORD="${ATS_PASSWORD:-admin1234}"

# ─── 0. Health (public) ─────────────────────────────────────────────────────
echo "=== HEALTH ==="
curl -s "$BASE/health" | jq .


# ─── 1. Login & get token ────────────────────────────────────────────────────
echo ""
echo "=== LOGIN ==="
TOKEN_RESP=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
echo "$TOKEN_RESP" | jq .
TOKEN=$(echo "$TOKEN_RESP" | jq -r .access_token)
echo "(token saved to \$TOKEN)"


# ─── 2. Who am I? ────────────────────────────────────────────────────────────
echo ""
echo "=== GET /auth/me ==="
curl -s "$BASE/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq .


# ─── 3. Create HR User ───────────────────────────────────────────────────────
echo ""
echo "=== POST /users (create HR) ==="
HR_RESP=$(curl -s -X POST "$BASE/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"hr@company.com","password":"hrpassword","role":"hr"}')
echo "$HR_RESP" | jq .
HR_ID=$(echo "$HR_RESP" | jq -r .id)


# ─── 4. Assign extra permissions to HR ───────────────────────────────────────
echo ""
echo "=== PUT /users/$HR_ID/permissions ==="
curl -s -X PUT "$BASE/users/$HR_ID/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission_codes":["taxonomy.manage","logs.view"]}' | jq .


# ─── 5. Job Description ──────────────────────────────────────────────────────
echo ""
echo "=== POST /job-descriptions ==="
JD_RESP=$(curl -s -X POST "$BASE/job-descriptions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Senior Python Engineer","raw_text":"We need 5 years Python, FastAPI, PostgreSQL, Docker..."}')
echo "$JD_RESP" | jq .
JD_ID=$(echo "$JD_RESP" | jq -r .id)


# ─── 6. Upload Resume ────────────────────────────────────────────────────────
echo ""
echo "=== POST /resumes (upload) ==="
RESUME_RESP=$(curl -s -X POST "$BASE/resumes" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/sample_resume.txt;type=text/plain")
echo "$RESUME_RESP" | jq .
RESUME_ID=$(echo "$RESUME_RESP" | jq -r .id)


# ─── 7. Create Analysis ──────────────────────────────────────────────────────
echo ""
echo "=== POST /analyses ==="
ANALYSIS_RESP=$(curl -s -X POST "$BASE/analyses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\":$RESUME_ID,\"job_description_id\":$JD_ID}")
echo "$ANALYSIS_RESP" | jq .
ANALYSIS_ID=$(echo "$ANALYSIS_RESP" | jq -r .id)


# ─── 8. Get Analysis result ──────────────────────────────────────────────────
echo ""
echo "=== GET /analyses/$ANALYSIS_ID ==="
curl -s "$BASE/analyses/$ANALYSIS_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .


# ─── 9. Get all results for a JD ─────────────────────────────────────────────
echo ""
echo "=== GET /results?job_description_id=$JD_ID ==="
curl -s "$BASE/results?job_description_id=$JD_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .


# ─── 10. Taxonomy ────────────────────────────────────────────────────────────
echo ""
echo "=== POST /taxonomy/skills ==="
SKILL_RESP=$(curl -s -X POST "$BASE/taxonomy/skills" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"FastAPI","category":"Backend","aliases":["fast-api","fastapi"]}')
echo "$SKILL_RESP" | jq .

echo ""
echo "=== GET /taxonomy/skills?q=fast ==="
curl -s "$BASE/taxonomy/skills?q=fast" \
  -H "Authorization: Bearer $TOKEN" | jq .


# ─── 11. Audit Logs (admin) ──────────────────────────────────────────────────
echo ""
echo "=== GET /logs/audit ==="
curl -s "$BASE/logs/audit?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .


# ─── 12. Logout ──────────────────────────────────────────────────────────────
echo ""
echo "=== POST /auth/logout ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "$BASE/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
