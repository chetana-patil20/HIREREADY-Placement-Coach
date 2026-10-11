"""Email delivery for account ownership verification."""
import smtplib
from email.message import EmailMessage

from app.config import settings


def send_verification_code(recipient: str, code: str) -> None:
    if not settings.email_enabled:
        raise RuntimeError("Email delivery is not configured. Add SMTP settings to backend/.env.")

    message = EmailMessage()
    message["Subject"] = "Verify your HireReady account"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = recipient
    message.set_content(
        "Use this code to verify your HireReady account: " + code +
        "\n\nThis code expires in 15 minutes. If you did not create this account, ignore this email."
    )
    smtp_factory = smtplib.SMTP_SSL if settings.SMTP_SSL else smtplib.SMTP
    with smtp_factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
        smtp.ehlo()
        if settings.SMTP_USE_TLS and not settings.SMTP_SSL:
            smtp.starttls()
            smtp.ehlo()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
