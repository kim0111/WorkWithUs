import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiosmtplib import SMTP as AioSMTP
from src.core.config import settings

logger = logging.getLogger(__name__)


async def _send_smtp(to_email: str, subject: str, html_body: str):
    """Async SMTP send — called from BackgroundTasks."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"SMTP not configured. Would send to {to_email}: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        smtp = AioSMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, start_tls=True)
        async with smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            await smtp.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")


# ── Email Templates ──────────────────────────────────

def _base_template(title: str, content: str) -> str:
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:600px;margin:0 auto;background:#0c0c0e;color:#f0ede8;padding:32px;border-radius:16px">
      <div style="text-align:center;margin-bottom:24px">
        <span style="display:inline-block;padding:8px 16px;background:#e8a838;color:#0c0c0e;border-radius:8px;font-weight:bold;font-size:18px">NexusHub</span>
      </div>
      <h2 style="color:#f0ede8;margin-bottom:16px">{title}</h2>
      <div style="color:#9a9898;line-height:1.7">{content}</div>
      <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:24px 0">
      <p style="color:#5e5c5c;font-size:12px;text-align:center">NexusHub Platform &copy; 2026</p>
    </div>
    """


async def send_verification_email(to_email: str, username: str, token: str):
    verify_url = f"http://localhost:3000/verify-email?token={token}"
    html = _base_template(
        "Verify Your Email",
        f"<p>Hi <strong>{username}</strong>,</p>"
        "<p>Please verify your email address to activate your account:</p>"
        f'<p><a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#e8a838;color:#0c0c0e;border-radius:8px;text-decoration:none;font-weight:bold">Verify Email →</a></p>'
        "<p>This link expires in 24 hours.</p>"
    )
    await _send_smtp(to_email, "Verify your NexusHub email", html)


async def send_welcome_email(to_email: str, username: str):
    html = _base_template(
        "Welcome to NexusHub!",
        f"<p>Hi <strong>{username}</strong>,</p>"
        "<p>Your account has been created successfully. Start exploring projects and building your portfolio!</p>"
        '<p><a href="http://localhost:3000/dashboard" style="color:#e8a838">Go to Dashboard →</a></p>'
    )
    await _send_smtp(to_email, "Welcome to NexusHub!", html)


async def send_application_status_email(to_email: str, username: str, project_title: str, status: str):
    color_map = {"accepted": "#4ade80", "rejected": "#f87171", "completed": "#60a5fa"}
    color = color_map.get(status, "#e8a838")
    html = _base_template(
        "Application Status Updated",
        f"<p>Hi <strong>{username}</strong>,</p>"
        f'<p>Your application for <strong>"{project_title}"</strong> has been updated:</p>'
        f'<p style="font-size:18px;color:{color};font-weight:bold">{status.upper()}</p>'
    )
    await _send_smtp(to_email, f"Application {status}: {project_title}", html)


async def send_new_application_email(to_email: str, owner_name: str, project_title: str, applicant_name: str):
    html = _base_template(
        "New Application Received",
        f"<p>Hi <strong>{owner_name}</strong>,</p>"
        f'<p><strong>{applicant_name}</strong> has applied to your project <strong>"{project_title}"</strong>.</p>'
        '<p><a href="http://localhost:3000/dashboard" style="color:#e8a838">Review Application →</a></p>'
    )
    await _send_smtp(to_email, f"New application: {project_title}", html)


async def send_chat_notification_email(to_email: str, username: str, sender_name: str, project_title: str):
    html = _base_template(
        "New Unread Message",
        f"<p>Hi <strong>{username}</strong>,</p>"
        f'<p>You have an unread message from <strong>{sender_name}</strong> '
        f'regarding project <strong>"{project_title}"</strong>.</p>'
        '<p><a href="http://localhost:3000/dashboard" style="color:#e8a838">Open Chat →</a></p>'
    )
    await _send_smtp(to_email, f"New message from {sender_name}", html)


async def send_submission_email(to_email: str, owner_name: str, project_title: str, student_name: str):
    html = _base_template(
        "Work Submitted for Review",
        f"<p>Hi <strong>{owner_name}</strong>,</p>"
        f'<p><strong>{student_name}</strong> has submitted their work for project <strong>"{project_title}"</strong>.</p>'
        "<p>Please review and approve or request revisions.</p>"
    )
    await _send_smtp(to_email, f"Submission ready: {project_title}", html)


async def send_review_email(to_email: str, username: str, reviewer_name: str, rating: float):
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    html = _base_template(
        "New Review Received",
        f"<p>Hi <strong>{username}</strong>,</p>"
        f"<p><strong>{reviewer_name}</strong> left you a review:</p>"
        f'<p style="font-size:24px;color:#e8a838">{stars} ({rating}/5)</p>'
    )
    await _send_smtp(to_email, f"New review from {reviewer_name}", html)
