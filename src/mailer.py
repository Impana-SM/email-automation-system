"""Production-ready asynchronous email dispatcher supporting SMTP and mock testing."""

import os
import logging
from email.message import EmailMessage
from typing import Optional, Tuple
from dotenv import load_dotenv
import aiosmtplib

load_dotenv()
logger = logging.getLogger("mailer")


class Mailer:
    """Asynchronous mail delivery service using aiosmtplib with fallback mock mode."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_mock: Optional[bool] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@emailautomation.com")
        
        env_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
        self.use_tls = use_tls if use_tls is not None else env_tls

        env_mock = os.getenv("USE_MOCK_EMAIL", "false").lower() in ("true", "1", "yes")
        self.use_mock = use_mock if use_mock is not None else env_mock

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Dispatches an email asynchronously.
        Returns a tuple of (success: bool, error_message: Optional[str]).
        """
        if self.use_mock:
            logger.info(
                "[MOCK EMAIL DISPATCH] Recipient: %s | Subject: %s | Content Length: %d chars",
                to_email,
                subject,
                len(body),
            )
            return True, None

        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        if is_html:
            # Set plain text alternative alongside HTML
            msg.set_content("Please view this email in an HTML-compatible client.")
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        try:
            # If port 465, use direct SSL; otherwise use STARTTLS
            use_direct_ssl = self.smtp_port == 465
            start_tls = self.use_tls and not use_direct_ssl

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user if self.smtp_user else None,
                password=self.smtp_password if self.smtp_password else None,
                use_tls=use_direct_ssl,
                start_tls=start_tls,
                timeout=15,
            )
            logger.info("Email successfully sent to %s via %s:%s", to_email, self.smtp_host, self.smtp_port)
            return True, None
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Failed to deliver email to %s: %s", to_email, error_msg)
            return False, error_msg


# Alias for backward compatibility
EmailService = Mailer
