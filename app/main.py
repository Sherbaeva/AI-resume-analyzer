"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(
    title="ATS — Resume Analyzer & Matching System",
    description="Backend API for resume analysis powered by n8n/OpenAI NLP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Bearer auth scheme visible in Swagger UI
_bearer_scheme = HTTPBearer()

# CORS — controlled via ALLOWED_ORIGINS env variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
