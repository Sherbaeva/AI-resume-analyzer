"""OTP generation, storage, and verification via Redis."""
import secrets
import string
import structlog
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()
log = structlog.get_logger()


OTP_PREFIX = "otp:"


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


def _key(email: str) -> str:
    return f"{OTP_PREFIX}{email.lower()}"


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure random numeric OTP code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


async def save_otp(email: str, code: str) -> None:
    """Store OTP in Redis with TTL."""
    log.info("redis.otp.save_attempt", email=email)
    async with _get_redis() as r:
        await r.setex(_key(email), settings.OTP_TTL_SECONDS, code)
    log.info("redis.otp.save_success", email=email)


async def verify_otp(email: str, code: str) -> bool:
    """
    Verify OTP code. Returns True if correct.
    Deletes the code on success (single-use).
    """
    log.info("redis.otp.verify_attempt", email=email)
    async with _get_redis() as r:
        stored = await r.get(_key(email))
        if stored and stored == code.strip():
            await r.delete(_key(email))
            log.info("redis.otp.verify_success", email=email)
            return True
        log.warning("redis.otp.verify_failed", email=email, exists_in_redis=bool(stored))
        return False


async def delete_otp(email: str) -> None:
    """Manually invalidate an OTP (e.g. on too many failed attempts)."""
    async with _get_redis() as r:
        await r.delete(_key(email))
