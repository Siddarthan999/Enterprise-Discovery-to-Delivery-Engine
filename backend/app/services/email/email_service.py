import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional
import os
from datetime import datetime
from dotenv import load_dotenv

# Email configuration - Update these with your Gmail SMTP settings
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")  # Your Gmail
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")  # Gmail App Password
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
SENDER_NAME = os.getenv("SENDER_NAME", "Enterprise OS")


async def send_sow_email(
    recipient_email: str,
    sender_name: str,
    doc_title: str,
    version: int,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    custom_message: Optional[str] = None
) -> bool:
    """
    Send SOW document via email with professional formatting
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{SENDER_EMAIL}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"Statement of Work: {doc_title} (Version {version})"

        # Email body
        if custom_message:
            body = custom_message
        else:
            body = f"""
Dear Recipient,

Please find attached the Statement of Work document for your review.

Document Details:
• Title: {doc_title}
• Version: {version}
• Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
• Format: {filename.split('.')[-1].upper()}

This document has been generated using our Enterprise OS platform and contains all the agreed-upon project specifications and deliverables.

Please review the attached document and feel free to reach out if you have any questions or require clarifications.

Best regards,
{sender_name}

---
This is an automated message from Enterprise OS.
Please do not reply directly to this email.
"""

        msg.attach(MIMEText(body, 'plain'))

        # Attach file
        attachment = MIMEApplication(file_bytes, _subtype=mime_type.split('/')[-1])
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attachment)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False