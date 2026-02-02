# Resume Analyzer - Software Architecture Document

## Executive Summary

This document outlines the comprehensive software architecture for the **Resume Analyzer** - an AI-powered hiring assistant that analyzes candidate resumes against job descriptions, provides match scoring, and enables side-by-side candidate comparison.

---

## 1. System Overview

### 1.1 Purpose
The Resume Analyzer helps recruiters and hiring managers efficiently evaluate candidates by:
- Automatically analyzing resumes against job descriptions
- Calculating match scores based on skills, experience, and qualifications
- Identifying matched and missing skills
- Enabling multi-candidate comparison
- Generating insights and exportable reports

### 1.2 Key Features
- AI-powered resume analysis
- Batch resume processing
- Real-time match scoring (65%-92% range)
- Skills gap identification
- Candidate ranking and comparison
- Dashboard analytics
- Export functionality

---

## 2. Architecture Patterns

### 2.1 Overall Architecture Style
- **Microservices Architecture**: Independent, scalable services
- **Event-Driven**: Asynchronous processing via message queues
- **API-First**: RESTful APIs with potential GraphQL for complex queries
- **Cloud-Native**: Containerized services (Docker/Kubernetes)

### 2.2 Design Principles
- **Separation of Concerns**: Clear service boundaries
- **Scalability**: Horizontal scaling for high-load services
- **Resilience**: Fault tolerance and circuit breakers
- **Security**: End-to-end encryption and authentication
- **Observability**: Comprehensive logging and monitoring

---

## 3. System Components

### 3.1 Client Layer

#### Web Application
- **Technology**: React.js with Next.js (SSR/SSG)
- **State Management**: Redux Toolkit or Zustand
- **UI Framework**: Tailwind CSS + shadcn/ui
- **Key Features**:
  - Resume upload (drag & drop)
  - Job description input
  - Real-time analysis progress
  - Interactive dashboards
  - Comparison views
  - Export functionality

#### Mobile Application (Optional Phase 2)
- **Technology**: React Native
- **Purpose**: On-the-go candidate review

---

### 3.2 API Gateway Layer

#### API Gateway
- **Technology**: Kong, AWS API Gateway, or NGINX
- **Responsibilities**:
  - Request routing
  - Rate limiting
  - Load balancing
  - Request/response transformation
  - API versioning

#### Authentication Service
- **Technology**: Node.js with Passport.js or Auth0
- **Authentication Methods**:
  - JWT tokens (access + refresh)
  - OAuth 2.0 (Google, Microsoft SSO)
  - Multi-factor authentication (MFA)
- **Security**:
  - Token encryption
  - Role-based access control (RBAC)
  - Session management

---

### 3.3 Application Services

#### Upload Service
- **Technology**: Node.js/Python FastAPI
- **Responsibilities**:
  - File upload handling
  - File validation (format, size)
  - Virus scanning
  - Metadata extraction
  - Storage orchestration
- **Supported Formats**: PDF, DOCX (max 10MB)

#### Analysis Engine
- **Technology**: Python (Django/FastAPI)
- **Core Functions**:
  - Orchestrate AI/ML pipeline
  - Calculate match scores
  - Aggregate analysis results
  - Generate insights
- **Performance**: Process resume in 3-5 seconds

#### Comparison Service
- **Technology**: Node.js/Python
- **Responsibilities**:
  - Multi-candidate data aggregation
  - Ranking algorithms
  - Statistical analysis
  - Generate comparison insights
- **Limits**: Up to 10 candidates per comparison

#### Export Service
- **Technology**: Node.js with libraries (PDFKit, ExcelJS)
- **Export Formats**:
  - PDF reports
  - Excel spreadsheets
  - CSV data
- **Features**: Custom branding, templates

#### Notification Service
- **Technology**: Node.js with SendGrid/AWS SES
- **Channels**:
  - Email notifications
  - Webhooks for integrations
  - In-app notifications

---

### 3.4 AI/ML Layer

#### NLP Service
- **Technology**: Python with spaCy, NLTK
- **Functions**:
  - Text extraction from documents
  - Entity recognition (skills, companies, education)
  - Text cleaning and normalization
  - Language detection

#### Embedding Service
- **Technology**: Python with Sentence Transformers
- **Models**: 
  - sentence-transformers/all-MiniLM-L6-v2
  - Custom fine-tuned models for domain-specific terms
- **Purpose**: Convert text to vector embeddings

#### Matching Algorithm
- **Technology**: Python (scikit-learn, custom algorithms)
- **Scoring Components**:
  - **Skills Match**: 40% weight
    - Exact skill matches
    - Semantic similarity
    - Skill level/proficiency
  - **Experience**: 30% weight
    - Years of experience
    - Relevant industry experience
  - **Education**: 15% weight
    - Degree relevance
    - Institution prestige (optional)
  - **Keywords**: 15% weight
    - Job-specific terminology
- **Output**: 0-100% match score

#### LLM Service
- **Technology**: Claude API / OpenAI GPT-4
- **Use Cases**:
  - Detailed resume summarization
  - Soft skill inference
  - Culture fit analysis
  - Generate recommendations
- **Rate Limiting**: Token-based quotas
- **Fallback**: Rule-based analysis if API unavailable

---

### 3.5 Data Processing

#### Document Parser
- **Technology**: Python with PyPDF2, python-docx, Apache Tika
- **Capabilities**:
  - PDF text extraction
  - DOCX parsing
  - Handle scanned documents (OCR via Tesseract)
  - Preserve formatting metadata

#### Data Extractor
- **Technology**: Python with custom NLP pipelines
- **Extraction Targets**:
  - Contact information
  - Work experience (company, role, duration)
  - Education (degree, institution, dates)
  - Skills (technical, soft skills)
  - Certifications
  - Projects

#### Message Queue
- **Technology**: RabbitMQ or Apache Kafka
- **Purpose**:
  - Asynchronous job processing
  - Decouple services
  - Handle traffic spikes
- **Queues**:
  - `resume_upload_queue`
  - `analysis_queue`
  - `notification_queue`
  - `export_queue`

---

### 3.6 Storage Layer

#### Primary Database
- **Technology**: PostgreSQL 15+
- **Schema Design**:
  - `users` - User accounts and profiles
  - `job_descriptions` - Stored job postings
  - `resumes` - Resume metadata and extracted data
  - `analyses` - Analysis results and scores
  - `comparisons` - Comparison sessions
  - `skills` - Normalized skills taxonomy
- **Features**:
  - JSONB for flexible data storage
  - Full-text search (tsvector)
  - Partitioning for large tables
  - Read replicas for scaling

#### Cache Layer
- **Technology**: Redis 7+
- **Use Cases**:
  - Session storage
  - API response caching
  - Rate limiting counters
  - Real-time leaderboards
  - Temporary analysis results
- **TTL Strategy**: 
  - Session: 24 hours
  - Analysis cache: 1 hour
  - Rate limits: 1 minute/hour windows

#### Vector Database
- **Technology**: Pinecone, Weaviate, or pgvector (PostgreSQL extension)
- **Purpose**:
  - Store resume embeddings
  - Store job description embeddings
  - Fast similarity search
  - Skill clustering
- **Indexing**: HNSW algorithm for approximate nearest neighbor search

#### Object Storage
- **Technology**: AWS S3, Azure Blob Storage, or MinIO (self-hosted)
- **Storage Structure**:
  - `/resumes/{user_id}/{resume_id}.pdf`
  - `/job-descriptions/{jd_id}.txt`
  - `/exports/{user_id}/{export_id}.pdf`
- **Features**:
  - Versioning enabled
  - Lifecycle policies (archive old files)
  - Encryption at rest
  - Pre-signed URLs for secure access

---

### 3.7 Analytics & Monitoring

#### Metrics Service
- **Technology**: Prometheus + Grafana
- **Metrics**:
  - API request rates
  - Service response times
  - Analysis processing time
  - Match score distributions
  - Error rates
  - Resource utilization

#### Logging
- **Technology**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Log Levels**: ERROR, WARN, INFO, DEBUG
- **Structured Logging**: JSON format
- **Retention**: 90 days

#### Analytics Dashboard
- **Technology**: Custom analytics service + BI tools
- **Insights**:
  - User engagement metrics
  - Most analyzed skills
  - Average match scores by role
  - Time-to-hire correlation
  - Feature usage statistics

---

## 4. Data Flow

### 4.1 Resume Analysis Flow

```
1. User uploads resume + job description
   ↓
2. Upload Service validates and stores in S3
   ↓
3. Message published to analysis_queue
   ↓
4. Document Parser extracts text
   ↓
5. Data Extractor pulls structured data
   ↓
6. NLP Service processes text
   ↓
7. Embedding Service creates vectors
   ↓
8. Matching Algorithm calculates scores
   ↓
9. LLM Service generates insights
   ↓
10. Results stored in PostgreSQL + Redis cache
    ↓
11. User notified, results displayed
```

### 4.2 Comparison Flow

```
1. User selects 2-3 candidates for comparison
   ↓
2. Comparison Service fetches analysis data
   ↓
3. Aggregates and ranks candidates
   ↓
4. Generates comparative insights
   ↓
5. Results cached and displayed
```

---

## 5. Technology Stack

### Backend
- **Languages**: Python 3.11+, Node.js 20+
- **Frameworks**: FastAPI, Express.js, Django
- **AI/ML**: spaCy, sentence-transformers, scikit-learn
- **APIs**: Claude API, OpenAI API

### Frontend
- **Framework**: React 18 with Next.js 14
- **Styling**: Tailwind CSS
- **Component Library**: shadcn/ui, Radix UI
- **State**: Redux Toolkit
- **Charts**: Recharts, Chart.js

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (EKS/GKE/AKS)
- **CI/CD**: GitHub Actions, GitLab CI
- **Infrastructure as Code**: Terraform
- **Service Mesh**: Istio (optional)

### Database & Storage
- **Primary DB**: PostgreSQL 15
- **Cache**: Redis 7
- **Vector DB**: Pinecone or pgvector
- **Object Storage**: AWS S3
- **Message Queue**: RabbitMQ

### Monitoring & DevOps
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack
- **Error Tracking**: Sentry
- **APM**: New Relic or Datadog

---

## 6. Security Architecture

### 6.1 Authentication & Authorization
- JWT-based authentication
- Refresh token rotation
- Role-based access control (Admin, Recruiter, Viewer)
- API key management for integrations

### 6.2 Data Security
- **Encryption in Transit**: TLS 1.3
- **Encryption at Rest**: AES-256
- **PII Protection**: Data anonymization options
- **GDPR Compliance**: Data deletion workflows

### 6.3 Application Security
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF tokens
- Rate limiting per user/IP
- DDoS protection (Cloudflare/AWS Shield)

### 6.4 File Security
- Virus/malware scanning (ClamAV)
- File type validation
- Size limits enforcement
- Sandboxed document processing

---

## 7. Scalability Considerations

### 7.1 Horizontal Scaling
- **Stateless Services**: All application services are stateless
- **Auto-scaling**: Kubernetes HPA based on CPU/memory/custom metrics
- **Database Scaling**: Read replicas, connection pooling

### 7.2 Performance Optimization
- **Caching Strategy**: Multi-layer caching (Redis, CDN)
- **CDN**: CloudFlare for static assets
- **Database Indexing**: Optimized indexes on frequent queries
- **Lazy Loading**: Paginated results

### 7.3 Load Distribution
- **Geographic Distribution**: Multi-region deployment
- **Load Balancing**: Application Load Balancer (ALB)
- **Queue-based Processing**: Async processing for heavy operations

---

## 8. Deployment Architecture

### 8.1 Environment Strategy
- **Development**: Local Docker Compose
- **Staging**: Kubernetes cluster (mimics production)
- **Production**: Multi-AZ Kubernetes deployment

### 8.2 CI/CD Pipeline
```
1. Code commit → GitHub
   ↓
2. Automated tests (unit, integration)
   ↓
3. Build Docker images
   ↓
4. Push to container registry
   ↓
5. Deploy to staging
   ↓
6. Automated E2E tests
   ↓
7. Manual approval
   ↓
8. Blue-green deployment to production
```

### 8.3 Disaster Recovery
- **Database Backups**: Daily automated backups, 30-day retention
- **Point-in-Time Recovery**: 5-minute recovery point objective
- **Multi-Region**: Active-passive setup
- **Backup Testing**: Monthly DR drills

---

## 9. API Design

### 9.1 Core Endpoints

#### Resume Analysis
```
POST /api/v1/analyze
- Body: { jobDescriptionId, resumeFiles[] }
- Response: { analysisId, status: "processing" }

GET /api/v1/analyze/{analysisId}
- Response: { matchScore, matchedSkills, missingSkills, experience }
```

#### Comparison
```
POST /api/v1/compare
- Body: { candidateIds[] }
- Response: { rankings, insights, skillComparison }
```

#### Export
```
POST /api/v1/export
- Body: { analysisIds[], format: "pdf"|"xlsx" }
- Response: { downloadUrl, expiresAt }
```

### 9.2 WebSocket Events (Real-time Updates)
```
ws://api.example.com/ws
- Event: analysis_progress { analysisId, progress: 45% }
- Event: analysis_complete { analysisId, results }
```

---

## 10. Future Enhancements

### Phase 2
- Resume builder integration
- Automated interview scheduling
- Video interview analysis (facial recognition, sentiment)
- Integration with ATS systems (Greenhouse, Lever)

### Phase 3
- Multi-language support
- Bias detection and mitigation
- Predictive analytics (success likelihood)
- Skills gap training recommendations
- Talent pool management

---

## 11. Cost Optimization

### Strategies
- **Compute**: Spot instances for non-critical batch jobs
- **Storage**: S3 lifecycle policies (move to Glacier after 90 days)
- **AI APIs**: Caching + fallback to cheaper models
- **Database**: Right-sized instances with auto-scaling
- **CDN**: Optimize asset delivery

### Estimated Monthly Cost (AWS, 1000 users)
- Compute (EKS): $800
- Database (RDS): $500
- Storage (S3): $200
- AI API calls: $1,500
- Monitoring/Logging: $300
- **Total**: ~$3,300/month

---

## 12. Compliance & Privacy

### Regulations
- **GDPR**: Right to deletion, data portability
- **CCPA**: California privacy compliance
- **SOC 2**: Security and availability controls

### Data Retention
- Resumes: 2 years (or until user deletion)
- Analysis results: 1 year
- Audit logs: 7 years

---

## Appendix A: Database Schema (Simplified)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Job Descriptions
CREATE TABLE job_descriptions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR(255),
  description TEXT,
  required_skills JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Resumes
CREATE TABLE resumes (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  file_url VARCHAR(500),
  candidate_name VARCHAR(255),
  candidate_email VARCHAR(255),
  extracted_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Analyses
CREATE TABLE analyses (
  id UUID PRIMARY KEY,
  job_description_id UUID REFERENCES job_descriptions(id),
  resume_id UUID REFERENCES resumes(id),
  match_score INTEGER,
  matched_skills JSONB,
  missing_skills JSONB,
  experience_years INTEGER,
  insights TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Comparisons
CREATE TABLE comparisons (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  analysis_ids UUID[],
  results JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Appendix B: Key Metrics & SLAs

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | < 200ms (p95) | Prometheus |
| Resume Analysis Time | < 5 seconds | Application logs |
| System Uptime | 99.9% | StatusPage |
| Database Query Time | < 50ms (p95) | PostgreSQL stats |
| Error Rate | < 0.1% | Sentry |

---

## Document Version
- **Version**: 1.0
- **Last Updated**: January 2026
- **Author**: System Architecture Team
- **Status**: Approved

---

## References
- [Microservices Best Practices](https://microservices.io)
- [AI/ML System Design](https://github.com/chiphuyen/machine-learning-systems-design)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Kubernetes Production Patterns](https://kubernetes.io/docs/concepts/)
