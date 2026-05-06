"""Email sending service using Resend HTTP API via httpx."""
import httpx
import structlog

from app.core.config import get_settings

settings = get_settings()


async def send_otp_email(to_email: str, otp_code: str) -> None:
    """Send OTP verification code to the user's email address via Resend HTTP API."""
    log = structlog.get_logger()
    log.info("email.otp.start", email=to_email)

    from_email = settings.SMTP_FROM or settings.SMTP_USER
    
    html_content = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 480px; margin: 40px auto; color: #333;">
      <h2 style="color: #1a1a2e;">CVPilot — Verification Code</h2>
      <p>Use the code below to complete your login:</p>
      <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                  margin: 24px 0; padding: 16px 24px; background: #f4f4f4;
                  border-radius: 8px; text-align: center; color: #1a1a2e;">
        {otp_code}
      </div>
      <p style="color: #666; font-size: 13px;">
        This code expires in <strong>{settings.OTP_TTL_SECONDS // 60} minutes</strong>.<br>
        If you did not attempt to log in, please ignore this email.
      </p>
    </body></html>
    """

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Your CVPilot verification code",
        "html": html_content,
        "text": (
            f"Your CVPilot login verification code is: {otp_code}\n\n"
            f"This code expires in {settings.OTP_TTL_SECONDS // 60} minutes."
        )
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.SMTP_PASSWORD}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10.0
            )
            resp.raise_for_status()
        log.info("email.otp.success", email=to_email)
    except Exception as exc:
        log.error("email.otp.failed", email=to_email, error=str(exc))
        raise
