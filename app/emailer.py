from email.message import EmailMessage

import aiosmtplib

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_STARTTLS


async def send_email(to_email: str, subject: str, body: str, cc: str | None = None):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.set_content(body)

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=SMTP_STARTTLS,
        username=SMTP_USER,
        password=SMTP_PASS,
    )
