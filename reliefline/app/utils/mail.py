"""
Minimal SMTP sender for the password-reset flow — plain smtplib against
whatever MAIL_* environment variables are set, no Flask-Mail dependency.

Returns False (never raises for "not configured") when MAIL_SERVER isn't
set, so callers can fall back to displaying the reset link directly. This
keeps the reset flow fully usable before any real mail server is wired up,
and it starts sending real email the moment MAIL_SERVER/MAIL_USERNAME/
MAIL_PASSWORD are added to .env — no code changes needed anywhere else.
"""
import os
import smtplib
from email.message import EmailMessage


def send_email(to_address, subject, body):
    server = os.getenv("MAIL_SERVER")
    if not server:
        return False

    port = int(os.getenv("MAIL_PORT", "587"))
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_SENDER", username or "no-reply@reliefline.local")
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() != "false"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP(server, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)
    return True
