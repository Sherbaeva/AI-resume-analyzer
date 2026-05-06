# CVPilot Project Report (ATS Resume Analyzer)
### What We Built, What We Used, and How We Did It — Explained Simply

---

## 🗂️ What Is This Project?

CVPilot is a system that automatically analyzes resumes. A recruiter uploads a job description and a candidate's resume, and the system compares them using Artificial Intelligence. It then produces a score: how well the resume matches the job, which skills align, and which are missing.

This document covers the **backend (server-side)** part of the project — the "brain" of the system that operates behind the scenes. Everything that happens on the website — logging in, uploading files, running analysis, storing data — is handled here.

---

## 🔧 What We Used and Why

### 1. Python + FastAPI — The Main Language and Framework
**What it is:** Python is one of the most popular programming languages in the world. FastAPI is a tool built on Python that allows developers to quickly create APIs — the "connectors" that allow the frontend (website) and mobile apps to talk to the backend.

**Why we used it:** All business logic — user authentication, resume uploads, running analysis, access control — is written here.

---

### 2. PostgreSQL — The Database
**What it is:** A digital "filing cabinet" where all system data is permanently stored: users, job descriptions, resumes, analysis results, and activity logs.

**Why we used it:** Without a database, all data would be lost every time the server restarts.

---

### 3. Redis — Fast Memory for Task Queuing
**What it is:** An extremely fast data store used to manage a "queue of tasks." Think of it like a digital waiting room — Redis manages the order in which tasks are processed.

**Why we used it:** When a request to analyze a resume comes in, it isn't processed immediately. Instead, it's placed in the Redis queue so the server doesn't get overwhelmed.

---

### 4. MinIO — File Storage
**What it is:** Our own private file storage system, similar to Google Drive or Dropbox, but running on our own server. It stores the actual resume files (PDF, DOCX, TXT).

**Why we used it:** Storing files directly in the database is slow and expensive. Instead, files live in MinIO, and the database only holds a reference (a link) to each file.

---

### 5. n8n — Automation and AI Analysis
**What it is:** A visual automation tool — like a digital assembly line where you connect steps together. It has built-in support for calling AI services like ChatGPT/OpenAI.

**Why we used it:** This is where the "smart" analysis happens. Our server sends n8n the resume text and job description → n8n forwards it to the AI (OpenAI/ChatGPT) → the AI evaluates the match → n8n sends the result back to our system.

---

### 6. Docker and Docker Compose — Containers
**What it is:** A technology that packages an application together with everything it needs to run into a self-contained "box" (called a container). This box works exactly the same on any computer or server.

**Why we used it:** Without Docker, each server would require hours of manual setup. With Docker, we run one command and everything starts automatically.

---

### 7. Nginx — The Gateway
**What it is:** A program that sits in front of all our services, receives requests from the internet, and routes them to the right place — like a receptionist directing visitors.

**Why we used it:** So that users can access the system via a clean address (`cvpilot.uz`) instead of memorizing technical port numbers and IP addresses.

---

### 8. GitLab — Code Storage and Version Control
**What it is:** A service where all project code is stored. Every change is saved with a description. You can roll back to any previous version at any time.

**Why we used it:** So multiple developers can work simultaneously without overwriting each other's work. It also provides a complete history of every change ever made.

---

## 📋 What We Did — Step by Step

### Stage 1: Architecture Planning
Before writing any code, we drew up a plan: what data needs to be stored, how it relates to other data, and how requests should flow through the system. We designed the database structure (tables and their relationships).

---

### Stage 2: Database Setup
We created all data tables in PostgreSQL:
- **users** — system users (recruiters, administrators)
- **job_descriptions** — job vacancy descriptions
- **resumes** — uploaded resume files and their metadata
- **analyses** — AI analysis results for resume-job pairs
- **skill_taxonomy** — a catalog of skills (Python, SQL, Excel, etc.)
- **audit_log** — a complete history of all actions (who did what, and when)

We also wrote a **migration system** — scripts that automatically update the database structure when the application starts. If we add a new field, it appears automatically without manual database changes.

---

### Stage 3: Authentication and Access Control (Auth + RBAC)
This was one of the most critical stages. We implemented:

**Login system (2-Step Verification):** A user enters their email and password → instead of immediately gaining access, a **6-digit one-time code (OTP)** is sent to their email address → the user enters the code → only then do they receive an access token. This is called Two-Factor Authentication (2FA) and adds an extra layer of security: even if someone's password is stolen, they still cannot log in without access to the registered email inbox.

**User roles:**
- `admin` — can see and do everything, manages other users
- `hr` — recruiter, can upload resumes, run analysis, view results

**Permission system (RBAC — Role-Based Access Control):** Every action in the system is protected. You cannot simply access anything — you need a specific permission code, for example `resumes.write` (to upload resumes) or `analysis.write` (to run analysis).

**Password security:** Passwords are stored in encrypted form (bcrypt). Not even we can read someone's password — we can only verify if it's correct.

**First admin account** is created automatically at startup using values from the configuration file.

---

### Stage 4: Resume Upload and Storage
We implemented file uploading:
- Supported formats: PDF, DOCX, TXT
- Files are automatically checked for size limits
- A unique "fingerprint" of each file (SHA-256 hash) is calculated — if the same file is uploaded again, the system recognizes it and avoids creating a duplicate
- The actual file is saved in MinIO
- The database only stores information about the file (name, size, location path)

---

### Stage 5: AI-Powered Resume Analysis
This is the "heart" of the system. The flow works like this:

1. A recruiter sends a request: "Analyze resume #5 against job description #3"
2. The system creates a task in the database with status `queued`
3. The task is placed into Redis and picked up by a **Celery worker** (background processor)
4. The worker sends the data to **n8n** via a webhook (a special URL for receiving data)
5. n8n processes the data through OpenAI/ChatGPT
6. The AI returns: a match score (%), matched skills, missing skills, and comments
7. n8n sends the result back to our system
8. The analysis status changes to `done`
9. The recruiter can now see the completed result

---

### Stage 6: Skills Catalog (Taxonomy)
We built a managed catalog of skills with categories (Backend, Frontend, Data Science, Soft Skills, etc.). An administrator can add new skills, edit them, or deactivate them. This ensures standardization — so "Python", "Python 3", and "python" are all recognized as the same skill.

---

### Stage 7: Activity Audit Log
Every action in the system is recorded: who logged in, who uploaded a resume, who triggered an analysis, who changed a user account, who deleted something. Each record includes the timestamp, IP address, and device information. This is critical for security and accountability.

---

### Stage 8: Production Deployment Setup
We created the configuration files needed to run the system on a real server:

- **`docker-compose.prod.yml`** — lists all services that must run (API, database, Redis, MinIO, n8n). Everything starts with one command.
- **`.env.prod`** — configuration file containing passwords, addresses, and secret keys. Intentionally not stored in GitLab for security reasons.
- **`nginx/ats.conf`** — configuration for the gateway.
- **`Dockerfile.prod`** — instructions for building our application into a container.
- **`entrypoint.sh`** — a startup script that: waits for the database to be ready → applies database updates → creates the first admin account → starts the web server.

---

### Stage 9: Deploying to the Production Server
**Production** means a real server accessible from the internet (as opposed to a test environment).

- Server: Ubuntu Linux at IP address `46.225.184.221`, domain: `cvpilot.uz`
- Cloned code from GitLab onto the server
- Configured the settings file (`.env.prod`)
- Started all containers with a single command
- Configured Nginx to route traffic from `cvpilot.uz` to our API
- Configured n8n — built the automation workflow for resume processing

---

### Stage 10: Bug Fixes and Improvements

During testing, we found and fixed the following issues:

| Problem | Solution |
|---|---|
| MinIO was missing from the production config | Added MinIO service to `docker-compose.prod.yml` |
| API started before MinIO was ready | Added a health check: API now waits for MinIO |
| A database field was renamed but the code wasn't updated | Fixed `entity` → `entity_type` throughout the codebase |
| No way to list all resumes or job descriptions | Added `GET /resumes` and `GET /job-descriptions` list endpoints |
| Swagger API docs were disabled on production | Re-enabled (needed by the frontend team) |
| CORS blocked frontend requests from local development | Added the correct allowed origins to the configuration |
| Wrong status code on failed login (401 instead of 400) | Fixed: 400 = wrong password, 401 = expired/missing token |
| Backend ports were exposed directly to the internet | Bound to `127.0.0.1` — only accessible through Nginx |

---

### Stage 11: Frontend Documentation
We wrote two documents for the frontend development team:

- **`docs/frontend-api.md`** — a complete reference of all API endpoints with request/response examples
- **`docs/AI_FRONTEND_PROMPT.md`** — an "AI prompt guide": a document the frontend developer can feed to their AI assistant, which will automatically understand how to connect to our API

---

## 📁 Final Project Structure

```
ATS System/
├── app/                    ← All server-side code
│   ├── api/               ← API endpoints (connection points)
│   ├── auth/              ← Authentication, tokens
│   ├── models/            ← Database table definitions
│   ├── repositories/      ← Database operations
│   ├── services/          ← Business logic
│   ├── schemas/           ← Data formats (what we accept/return)
│   └── tests/             ← Automated tests
├── alembic/               ← Database migration scripts
├── nginx/                 ← Gateway configuration
├── docs/                  ← All documentation
├── docker-compose.yml     ← Development startup
├── docker-compose.prod.yml← Production startup
├── Dockerfile.prod        ← Build instructions
└── .env.prod.example      ← Configuration template
```

---

## 🔐 Security Measures Implemented

- All passwords are stored encrypted — impossible to read even by us
- **Two-Factor Authentication (2FA):** Login requires both the correct password and a one-time code sent to the user's email — meaning a stolen password alone is not enough to break in
- Sessions use short-lived tokens (60 minutes), not permanent cookies
- Every action is verified against a permission before it's allowed
- Internal services (database, Redis, MinIO) are not accessible from the internet directly
- All actions are logged in the audit trail
- Configuration files containing passwords are excluded from GitLab

---
```markdown
## 🏁 Conclusion

The CV Pilot backend is now fully operational, providing a secure and scalable foundation for the ATS platform. With the API and AI prompts documented, the project is ready for frontend integration and final deployment.
```
