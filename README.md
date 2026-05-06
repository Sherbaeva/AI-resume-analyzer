# ATS — Resume Analyzer & Matching System

> **Stack:** FastAPI · PostgreSQL · Redis · Celery · n8n · MinIO (S3)  
> **Auth:** JWT (Bearer) · RBAC (roles + per-user permissions) · Audit Logs

| | Dev | Prod |
|---|---|---|
| **API** | http://localhost:8000 | https://api.yourdomain.com |
| **Swagger** | http://localhost:8000/docs | скрыт |
| **MinIO Console** | http://localhost:9101 | http://server:9101 |
| **n8n** | http://localhost:5678 | https://n8n.yourdomain.com |

---

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Auth & RBAC](#auth--rbac)
4. [Конфигурация](#конфигурация)
5. [Запуск и управление](#запуск-и-управление)
6. [API Reference](#api-reference)
7. [Для фронтендера](#для-фронтендера)
8. [Хранилище файлов (MinIO / S3)](#хранилище-файлов-minio--s3)
9. [Настройка n8n](#настройка-n8n)
10. [Тесты](#тесты)
11. [Деплой на прод](#деплой-на-прод)
12. [Структура проекта](#структура-проекта)

---

## Быстрый старт

```bash
# 1. Конфиг
cp .env.example .env   # (или .env уже есть с дефолтами)

# 2. Поднять все сервисы
docker-compose up --build -d

# 3. Применить миграции + создать первого admin + засидить permissions
#    (entrypoint.sh делает это автоматически, но можно вручную):
docker-compose exec api alembic upgrade head
docker-compose exec api python tools/bootstrap.py

# 4. Проверить
curl http://localhost:8000/health
# → {"status":"ok","service":"ats-backend"}

# 5. Войти
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ats-system.com","password":"admin1234"}'
# → {"access_token":"eyJ...","token_type":"bearer","expires_in":3600}
```

> **Первый admin** создаётся автоматически при старте из `.env`:  
> `ADMIN_BOOTSTRAP_EMAIL=admin@ats-system.com` / `ADMIN_BOOTSTRAP_PASSWORD=admin1234`

---

## Архитектура

```
┌──────────────┐   JWT REST API   ┌──────────────────────────────────────────┐
│   Frontend   │ ◄──────────────► │  Backend  FastAPI :8000                  │
└──────────────┘                  │                                          │
                                  │  ┌──────────┐  ┌────────────────────┐  │
                                  │  │PostgreSQL│  │MinIO / S3 Storage  │  │
                                  │  └──────────┘  └────────────────────┘  │
                                  │                                          │
                                  │  ── POST webhook ──────────────────────► │
                                  └──────────────────────────────────────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │   n8n Worker    │
                                          │  (NLP / OpenAI) │
                                          └────────┬────────┘
                                                   │ POST /api/internal/analysis-callback
                                                   ▼
                                          (Backend обновляет Analysis)
```

**Принцип:** Frontend → Backend (JWT REST). Backend → n8n (webhook). n8n → Backend (секретный callback).  
Фронт **никогда не обращается к n8n напрямую.**

---

## Auth & RBAC

### Роли

| Роль | Права по умолчанию |
|------|--------------------|
| `admin` | Все 11 permissions |
| `hr` | `jd.write` · `jd.read` · `resumes.read` · `resumes.write` · `analysis.write` · `results.read` · `taxonomy.read` |

Admin может выдать HR дополнительные права через `PUT /users/{id}/permissions`.

### Все permission коды

```
users.manage   resumes.read    resumes.write   resumes.delete
taxonomy.manage  taxonomy.read  logs.view
jd.write  jd.read  analysis.write  results.read
```

### Получить токен

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ats-system.com","password":"admin1234"}'
```

### Использовать токен

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

### Bootstrap

```bash
# Засидить permissions + создать admin (если users пустая):
docker-compose exec api python tools/bootstrap.py
```

---

## Конфигурация

Файл `.env` (создаётся из `.env.example`):

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | PostgreSQL (asyncpg) | `postgresql+asyncpg://ats_user:ats_pass@postgres:5432/ats_db` |
| `REDIS_URL` | Redis | `redis://redis:6379/0` |
| `STORAGE_DIR` | Локальная папка (fallback если S3 не задан) | `storage` |
| `BACKEND_URL` | Внешний URL backend (для callback) | `http://api:8000` |
| `N8N_WEBHOOK_URL` | URL webhook n8n | `http://n8n:5678/webhook-test/resume-analyze` |
| `N8N_SECRET` | Секрет для валидации n8n callback | `change_me_in_production` |
| `MAX_UPLOAD_MB` | Максимальный размер резюме (МБ) | `10` |
| `ALLOWED_ORIGINS` | CORS origins (через запятую, или `*`) | `*` |
| **JWT** | | |
| `JWT_SECRET` | Секрет подписи JWT | `change_me_in_production...` |
| `JWT_ALG` | Алгоритм | `HS256` |
| `JWT_EXPIRES_MIN` | Время жизни токена (минуты) | `60` |
| **Admin** | | |
| `ADMIN_BOOTSTRAP_EMAIL` | Email первого admin | `admin@ats-system.com` |
| `ADMIN_BOOTSTRAP_PASSWORD` | Пароль первого admin | `admin1234` |
| **MinIO / S3** | | |
| `S3_BUCKET_NAME` | Имя бакета (пустая → локальный диск) | `ats-resumes` |
| `S3_ACCESS_KEY` | Access key | `minio_admin` |
| `S3_SECRET_KEY` | Secret key | `minio_password` |
| `S3_ENDPOINT_URL` | Endpoint (для MinIO) | `http://minio:9000` |
| `S3_REGION` | Регион | `us-east-1` |
| `S3_PUBLIC_URL` | Публичный URL (CDN, опционально) | `` |
| `ENVIRONMENT` | `development` / `production` | `development` |

---

## Запуск и управление

```bash
# Поднять всё
docker-compose up --build -d

# Статус
docker-compose ps

# Логи API в реальном времени
docker-compose logs -f api

# Миграции
docker-compose exec api alembic upgrade head
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic current

# Bootstrap (permissions + admin)
docker-compose exec api python tools/bootstrap.py

# Остановить
docker-compose down

# Makefile (если используется)
make dev          # docker-compose up
make prod         # docker-compose -f docker-compose.prod.yml up
make down         # stop all
make migrate      # alembic upgrade head
make logs         # logs api
make shell        # bash in api container
make test         # pytest
```

### Контейнеры

| Контейнер | Роль | Порт (внешний) |
|---|---|---|
| `ats_api` | FastAPI 🔒 JWT auth | `8000` |
| `ats_worker` | Celery worker | — |
| `ats_postgres` | PostgreSQL | `5433` |
| `ats_redis` | Redis | `6379` |
| `ats_minio` | MinIO S3 storage | `9100` (API) · `9101` (Console) |
| `ats_n8n` | n8n workflow | `5678` |

---

## API Reference

### Полный флоу

```
POST /auth/login                          → access_token
POST /job-descriptions          🔒 jd.write     → jd_id
POST /resumes                   🔒 resumes.write  → resume_id
POST /analyses                  🔒 analysis.write → analysis_id (idempotent)
GET  /analyses/{id}             🔒 results.read   → poll до status=done|failed
GET  /results?job_description_id=N 🔒 results.read → все анализы для JD
```

---

### GET /health — публичный
```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"ats-backend"}
```

---

### POST /auth/login — публичный
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ats-system.com","password":"admin1234"}'
```
```json
{"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}
```

### GET /auth/me 🔒
```bash
curl http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"
```
```json
{"id":1,"email":"admin@ats-system.com","role":"admin","is_active":true,"permissions":["analysis.write",...]}
```

---

### POST /job-descriptions 🔒 (`jd.write`)
```bash
curl -X POST http://localhost:8000/job-descriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Backend Engineer","raw_text":"Python, FastAPI, PostgreSQL..."}'
```

### POST /resumes 🔒 (`resumes.write`)
```bash
curl -X POST http://localhost:8000/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/resume.pdf"
```
Форматы: **PDF, DOCX, TXT**. Лимит: **10 МБ**.  
Дедупликация по SHA-256: тот же файл → тот же `resume_id`.

### POST /analyses 🔒 (`analysis.write`)
```bash
curl -X POST http://localhost:8000/analyses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_id":1,"job_description_id":1}'
```

### GET /analyses/{id} 🔒 (`results.read`)
```json
{
  "id": 1, "status": "done", "score": 85.5,
  "matched_skills_json": "[\"Python\",\"FastAPI\"]",
  "missing_skills_json": "[\"Kubernetes\"]",
  "explanations_json": "{\"summary\":\"Strong match\"}"
}
```
> Статусы: `queued` → `running` → `done` | `failed`

---

### Users API (admin — `users.manage`)

```bash
POST   /users                    # создать пользователя
GET    /users                    # список
GET    /users/{id}
PATCH  /users/{id}               # изменить role/is_active/password
DELETE /users/{id}               # деактивировать (soft)
GET    /users/{id}/permissions
PUT    /users/{id}/permissions   # {"permission_codes": ["taxonomy.manage"]}
```

### Taxonomy API (`taxonomy.read` / `taxonomy.manage`)

```bash
GET    /taxonomy/skills          # ?q=python&category=Backend&is_active=true
GET    /taxonomy/skills/{id}
POST   /taxonomy/skills          # admin: {"name":"FastAPI","category":"Backend"}
PATCH  /taxonomy/skills/{id}     # admin
DELETE /taxonomy/skills/{id}     # admin (soft delete)
```

### Audit Logs (`logs.view` — admin)

```bash
GET /logs/audit?action=auth.login&limit=50&offset=0
# Фильтры: action, entity_type, actor_user_id, date_from, date_to
```

---

### POST /api/internal/analysis-callback ⚠️ ТОЛЬКО ДЛЯ n8n

```bash
# НЕ вызывать с фронта. Требует X-N8N-SECRET заголовок.
curl -X POST http://localhost:8000/api/internal/analysis-callback \
  -H "X-N8N-SECRET: your_secret" \
  -H "Content-Type: application/json" \
  -d '{"analysis_id":1,"status":"done","score":85.5,"matched_skills":["Python"]}'
```

---

## Для фронтендера

### Быстрый старт с SDK

```bash
# Скопировать SDK в проект фронта
cp sdk/ts/types.ts  src/api/types.ts
cp sdk/ts/client.ts src/api/client.ts
# Нет зависимостей — только нативный fetch
```

```ts
import { AtsClient, persistToken, clearToken } from './api/client'

const api = new AtsClient(import.meta.env.VITE_API_URL)

// Логин
const { access_token } = await api.login('hr@company.com', 'password')
persistToken(access_token)          // сохраняет в localStorage

// Кто я?
const me = await api.me()
console.log(me.role)                // "hr"
console.log(me.permissions)        // ["resumes.read", ...]

// RBAC guard
if (me.permissions.includes('taxonomy.manage')) {
  await api.createSkill({ name: 'FastAPI', category: 'Backend' })
}

// Полный флоу анализа
const jd     = await api.createJobDescription({ title: 'Engineer', raw_text: '...' })
const resume = await api.uploadResume(file)
const a      = await api.createAnalysis({ resume_id: resume.id, job_description_id: jd.id })

// Поллинг
const poll = setInterval(async () => {
  const res = await api.getAnalysis(a.id)
  if (res.status === 'done' || res.status === 'failed') {
    clearInterval(poll)
    console.log('Score:', res.score)
  }
}, 2000)
setTimeout(() => clearInterval(poll), 5 * 60 * 1000) // timeout 5 мин

// Logout
await api.logout()
clearToken()
```

### Важно: JSON-строки в ответе анализа

`matched_skills_json`, `missing_skills_json`, `explanations_json` — это **строки**, нужно `JSON.parse()`:
```ts
const matched = JSON.parse(analysis.matched_skills_json ?? '[]')
```

### Ошибки

| Код | Значение |
|-----|---------|
| `401` | Нет токена или истёк → перенаправить на `/login` |
| `403` | Не хватает permission → показать `"Недостаточно прав"` |
| `409` | Дубликат (email, название скилла) |
| `422` | Ошибка валидации → `response.detail[].msg` |

### Файлы для фронтенда

```
sdk/ts/types.ts                       ← TypeScript типы всех схем
sdk/ts/client.ts                      ← AtsClient класс, persistToken/clearToken
docs/frontend-api.md                  ← Полный API reference
docs/frontend-api.postman.json        ← Postman коллекция
docs/curl-examples.sh                 ← Bash-скрипт всех примеров
docs/frontend-integration-checklist  ← Чеклист перед деплоем
```

---

## Хранилище файлов (MinIO / S3)

По умолчанию файлы резюме хранятся в **MinIO** (локальный S3-совместимый сервер).

| | Dev | Prod |
|---|---|---|
| **MinIO API** | http://localhost:9100 | внутри Docker: `minio:9000` |
| **MinIO Console** | http://localhost:9101 | `http://server:9101` |
| **Логин** | `minio_admin` / `minio_password` | задать в `.env.prod` |

Бакет `ats-resumes` создаётся **автоматически** при первой загрузке.

**Переключение хранилища:**
```env
S3_BUCKET_NAME=ats-resumes   # → MinIO / S3
S3_BUCKET_NAME=              # → локальный диск (storage/)
```

**Подключить AWS S3 / Cloudflare R2:**
```env
S3_BUCKET_NAME=my-bucket
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_ENDPOINT_URL=             # пусто для AWS; для R2: https://<account>.r2.cloudflarestorage.com
S3_REGION=eu-west-1
```

---

## Настройка n8n

1. Открыть http://localhost:5678
2. Создать **Webhook** узел:
   - Method: `POST`, Path: `resume-analyze`
3. Добавить **OpenAI** узел — использовать `{{ $json.resume_text }}` и `{{ $json.job_text }}`
4. Добавить **HTTP Request** для callback:

```
Method:  POST
URL:     {{ $json.callback_url }}
Headers: X-N8N-SECRET: <N8N_SECRET из .env>

Body:
{
  "analysis_id": {{ $json.analysis_id }},
  "status":         "done",
  "score":           85.5,
  "matched_skills":  ["Python", "FastAPI"],
  "missing_skills":  ["Kubernetes"],
  "explanations":    {"summary": "Strong match"}
}
```

5. **Активировать** workflow (кнопка Active)  
6. В проде — изменить URL с `/webhook-test/` на `/webhook/` и обновить `N8N_WEBHOOK_URL` в `.env.prod`

---

## Тесты

```bash
# Без Docker (используют SQLite in-memory)
pip install -r requirements.txt
pytest app/tests/ -v

# Покрытие
pytest --cov=app app/tests/
```

Тестовые файлы:

| Файл | Что проверяет |
|---|---|
| `test_auth.py` | login success/fail, /me с токеном и без, logout |
| `test_users.py` | Admin CRUD, HR → 403, duplicate email, deactivate |
| `test_rbac.py` | Permission guards, HR с/без escalation, 401 без токена |
| `test_taxonomy.py` | taxonomy.read для HR, taxonomy.manage только admin |
| `test_health.py` | `GET /health` |
| `test_resume_upload.py` | загрузка, тип, размер, soft delete |
| `test_create_analysis.py` | создание анализа, n8n mock |
| `test_analysis_callback.py` | callback done/failed/wrong secret |
| `test_idempotency.py` | повторный вызов → тот же analysis_id |

---

## Деплой на прод

```bash
# На сервере: 46.225.184.221
git clone https://gitlab.com/bratskayapomosh/resume-analyzer-for-efficient-hiring.git
cd resume-analyzer-for-efficient-hiring
cp .env.prod.example .env.prod
nano .env.prod   # Заполнить все секреты

# Обязательно задать:
# JWT_SECRET=$(openssl rand -hex 32)
# ADMIN_BOOTSTRAP_EMAIL=admin@company.com
# ADMIN_BOOTSTRAP_PASSWORD=<strong>
# POSTGRES_PASSWORD=<strong>
# S3_ACCESS_KEY=<minio key>
# S3_SECRET_KEY=<minio secret>
# ALLOWED_ORIGINS=https://yourfrontend.com

docker-compose -f docker-compose.prod.yml up --build -d

# Миграции + bootstrap запустятся автоматически через entrypoint.sh
```

> **Firewall:** закрыть порты `5432`, `6379`, `9100` — только для внутреннего Docker.  
> Наружу открыть `8000` (API) и при необходимости `9101` (MinIO Console).

---

## Структура проекта

```
app/
├── api/
│   ├── internal/callback.py       ← POST /api/internal (только n8n)
│   ├── v1/analyses.py             ← /analyses, /results  🔒
│   ├── v1/health.py               ← /health  (public)
│   ├── v1/job_descriptions.py     ← /job-descriptions    🔒
│   ├── v1/resumes.py              ← /resumes             🔒
│   └── router.py
├── auth/
│   ├── dependencies.py            ← get_current_user, require_role, require_permission
│   ├── jwt.py                     ← create/decode token
│   ├── password.py                ← bcrypt hash/verify
│   ├── router.py                  ← /auth/login, /auth/me, /auth/logout
│   └── schemas.py
├── audit/
│   └── service.py                 ← write_audit() утилита
├── core/
│   ├── config.py                  ← pydantic-settings (.env)
│   ├── database.py
│   ├── logging.py
│   └── redis.py
├── logs/
│   └── router.py                  ← GET /logs/audit  🔒 (admin)
├── models/
│   ├── analysis.py
│   ├── audit_log.py               ← расширен: actor_user_id, meta_json, ip, user_agent
│   ├── job_description.py
│   ├── permission.py              ← Permission, UserPermission
│   ├── resume.py
│   ├── skill_taxonomy.py          ← SkillTaxonomy
│   └── user.py                    ← User, UserRole enum
├── parsers/                       ← PDF, DOCX, TXT парсеры
├── rbac/
│   ├── permissions.py             ← ALL_PERMISSIONS, ROLE_DEFAULTS
│   └── service.py                 ← get_effective_permissions()
├── repositories/
│   ├── audit_log_repo.py
│   ├── job_description_repo.py
│   ├── permission_repo.py         ← seed permissions
│   ├── resume_repo.py
│   ├── taxonomy_repo.py           ← list/create/update skills
│   └── user_repo.py               ← CRUD users + permissions
├── schemas/
├── services/
│   ├── analysis_service.py
│   ├── n8n_service.py
│   └── resume_service.py
├── storage/
│   ├── base.py                    ← StorageService ABC
│   ├── factory.py                 ← get_storage() → S3 или Local
│   ├── local.py                   ← LocalStorageService
│   └── s3.py                      ← S3StorageService (MinIO/AWS/R2)
├── taxonomy/
│   ├── router.py                  ← /taxonomy/skills  🔒
│   └── schemas.py
├── tests/                         ← pytest-asyncio
├── users/
│   ├── router.py                  ← /users CRUD 🔒 (admin)
│   └── schemas.py
├── workers/
└── main.py

alembic/versions/
├── 001_initial.py
└── 002_auth_rbac.py               ← users, permissions, user_permissions, skill_taxonomy

docs/
├── frontend-api.md
├── frontend-api.postman.json
├── frontend-integration-checklist.md
└── curl-examples.sh

sdk/ts/
├── client.ts                      ← AtsClient (все методы)
└── types.ts                       ← TypeScript типы

tools/
├── bootstrap.py                   ← seed permissions + create admin
└── generate_frontend_pack.py

Makefile
docker-compose.yml
docker-compose.prod.yml
entrypoint.sh                      ← wait → migrate → bootstrap → uvicorn
.env.prod.example
```
