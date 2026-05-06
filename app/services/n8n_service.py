"""n8n webhook caller service."""
import httpx
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class N8nService:
    async def trigger_analysis(
        self,
        analysis_id: int,
        resume_text: str,
        job_text: str,
    ) -> None:
        payload = {
            "analysis_id": analysis_id,
            "resume_text": resume_text,
            "job_text": job_text,
            "callback_url": settings.analysis_callback_url,
        }
        logger.info("Triggering n8n analysis", analysis_id=analysis_id)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.N8N_WEBHOOK_URL, json=payload)
            response.raise_for_status()
        logger.info("n8n webhook triggered successfully", analysis_id=analysis_id)
