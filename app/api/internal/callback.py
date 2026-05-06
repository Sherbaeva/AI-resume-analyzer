"""Internal callback endpoint called by n8n after analysis completion."""
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import get_settings
from app.schemas.analysis import AnalysisCallbackPayload, AnalysisResponse
from app.services.analysis_service import AnalysisService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/internal", tags=["Internal"])
settings = get_settings()


def _verify_secret(x_n8n_secret: str = Header(..., alias="X-N8N-SECRET")) -> None:
    if x_n8n_secret != settings.N8N_SECRET:
        logger.warning("Invalid n8n secret received")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid N8N secret",
        )


@router.post(
    "/analysis-callback",
    response_model=AnalysisResponse,
    dependencies=[Depends(_verify_secret)],
)
async def analysis_callback(
    payload: AnalysisCallbackPayload,
    db: AsyncSession = Depends(get_session),
):
    """Receive analysis results from n8n. Requires X-N8N-SECRET header."""
    service = AnalysisService(db)
    analysis = await service.handle_callback(payload)
    return analysis
