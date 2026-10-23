# Sends emails (only when mail settings are set up).

import os
import smtplib
from email.message import EmailMessage


# Sends an email using the MAIL_* settings in .env.
# If email isn't set up, it does nothing and returns False (the app then shows the info on screen instead).
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
