"""Central API router aggregating all sub-routers."""
from fastapi import APIRouter
from app.api.v1 import job_descriptions, resumes, analyses, health
from app.api.internal import callback
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.taxonomy.router import router as taxonomy_router
from app.logs.router import router as logs_router

api_router = APIRouter()

# Auth endpoints (public)
api_router.include_router(auth_router)

# Public health check
api_router.include_router(health.router)

# Protected v1 endpoints
api_router.include_router(job_descriptions.router)
api_router.include_router(resumes.router)
api_router.include_router(analyses.router)

# Admin endpoints
api_router.include_router(users_router)
api_router.include_router(taxonomy_router)
api_router.include_router(logs_router)

# Internal n8n callback (secret header, no JWT)
api_router.include_router(callback.router)
