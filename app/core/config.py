"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ats_user:ats_pass@postgres:5432/ats_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Storage
    STORAGE_DIR: str = "storage"

    # Backend self-reference URL (used for callback URL sent to n8n)
    BACKEND_URL: str = "http://api:8000"

    # n8n
    N8N_WEBHOOK_URL: str = "http://n8n:5678/webhook/resume-analyze"
    N8N_SECRET: str = "change_me_in_production"

    # Upload limits
    MAX_UPLOAD_MB: int = 10

    # CORS — comma-separated origins, e.g. https://yourdomain.com,https://app.yourdomain.com
    # Use * for development only
    ALLOWED_ORIGINS: str = "*"

    # S3 / MinIO storage (leave S3_BUCKET_NAME empty to use local filesystem)
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: str = ""  # http://minio:9000 for MinIO, empty for AWS
    S3_REGION: str = "us-east-1"
    S3_PUBLIC_URL: str = ""    # optional CDN/public URL prefix

    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # JWT
    JWT_SECRET: str = "change_me_in_production_use_openssl_rand_hex_32"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60  # 1 hour

    # Bootstrap admin (created if users table is empty)
    ADMIN_BOOTSTRAP_EMAIL: str = "admin@ats-system.com"
    ADMIN_BOOTSTRAP_PASSWORD: str = "admin1234"

    # Email / SMTP (for OTP 2FA via Resend)
    SMTP_HOST: str = "smtp.resend.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "resend"      # Resend always uses "resend" as user
    SMTP_PASSWORD: str = ""        # Resend API Key
    SMTP_FROM: str = ""            # e.g. CVPilot <onboarding@resend.dev>
    OTP_TTL_SECONDS: int = 300     # OTP expires after 5 minutes

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def analysis_callback_url(self) -> str:
        return f"{self.BACKEND_URL}/api/internal/analysis-callback"

    @property
    def cors_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
