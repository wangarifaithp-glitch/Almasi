import html
import httpx

from app.core.config import Settings

RESEND_API_URL = "https://api.resend.com/emails"


async def send_password_reset_email(
    settings: Settings, recipient: str, name: str, reset_url: str
) -> None:
    if not settings.resend_api_key or not settings.resend_from_email:
        raise RuntimeError("RESEND_API_KEY and RESEND_FROM_EMAIL must be configured.")

    safe_name = html.escape(name)
    safe_url = html.escape(reset_url, quote=True)
    payload = {
        "from": settings.resend_from_email,
        "to": [recipient],
        "subject": "Reset your ALMASI password",
        "html": (
            f"<p>Hello {safe_name},</p>"
            "<p>We received a request to reset your ALMASI password. "
            "Use the secure link below within 30 minutes:</p>"
            f'<p><a href="{safe_url}">Reset your password</a></p>'
            "<p>If you didn’t request this, you can ignore this email.</p>"
        ),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        )
    response.raise_for_status()


async def send_verification_email(
    settings: Settings, recipient: str, name: str, verification_url: str
) -> None:
    if not settings.resend_api_key or not settings.resend_from_email:
        raise RuntimeError("RESEND_API_KEY and RESEND_FROM_EMAIL must be configured.")
    safe_name = html.escape(name)
    safe_url = html.escape(verification_url, quote=True)
    payload = {
        "from": settings.resend_from_email,
        "to": [recipient],
        "subject": "Verify your ALMASI email",
        "html": (
            f"<p>Hello {safe_name},</p>"
            "<p>Verify your email address to activate your ALMASI learner account:</p>"
            f'<p><a href="{safe_url}">Verify my email</a></p>'
            "<p>This link expires in 24 hours.</p>"
        ),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"******"},
        )
    response.raise_for_status()
