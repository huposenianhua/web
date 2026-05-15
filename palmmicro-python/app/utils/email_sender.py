"""Email sending utility.

Translated from PHP email.php.
Provides HTML email composition and sending via SMTP.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from textwrap import fill

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "woody@palmmicro.com"

# SMTP configuration (should be set via environment variables or config)
_SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
_SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
_SMTP_USER = os.environ.get("SMTP_USER", "")
_SMTP_PASS = os.environ.get("SMTP_PASS", "")


def _build_html(subject: str, contents: str) -> str:
    """Wrap subject and contents into a complete HTML document.

    Translated from PHP EmailHtml() HTML structure:
        <html><head><title>subject</title></head>
        <body><div>contents</div></body></html>
    """
    html = f"<html>\n"
    html += f"<head><title>{subject}</title></head>\n"
    html += f"<body><div>{contents}</div></body>\n"
    html += f"</html>"
    return html


def email_html(to: str, subject: str, contents: str) -> bool:
    """Send an HTML email.

    Translated from PHP EmailHtml().

    Args:
        to: Recipient email address.
        subject: Email subject line.
        contents: HTML body contents (will be wrapped in <div>).

    Returns:
        True if sent successfully, False otherwise.
    """
    eol = "\r\n"
    html_body = _build_html(subject, contents)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = ADMIN_EMAIL
    msg["To"] = to
    msg["Reply-To"] = ADMIN_EMAIL
    msg["X-Mailer"] = "Python"

    # Wrap long lines like PHP wordwrap($strMessage, 70, $eol)
    wrapped = fill(html_body, width=70, break_long_words=False,
                   replace_whitespace=False)

    part = MIMEText(wrapped, "html", "utf-8")
    msg.attach(part)

    try:
        if _SMTP_USER and _SMTP_PASS:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                server.starttls()
                server.login(_SMTP_USER, _SMTP_PASS)
                server.sendmail(ADMIN_EMAIL, [to], msg.as_string())
        else:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                server.sendmail(ADMIN_EMAIL, [to], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError) as exc:
        import logging
        logging.getLogger(__name__).error("Email send failed: %s", exc)
        return False
