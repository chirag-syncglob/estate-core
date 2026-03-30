from __future__ import annotations

import html
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import lru_cache
from pathlib import Path
from string import Template


class EmailUtil:
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

    def __init__(
        self,
        host: str | None,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str | None,
        from_name: str = "Estate Core",
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    def _ensure_configured(self) -> None:
        if not self.host or not self.from_email:
            raise ValueError("SMTP configuration is incomplete")

        if self.username and not self.password:
            raise ValueError("SMTP password is required when SMTP username is set")

    def _build_sender(self) -> str:
        return f"{self.from_name} <{self.from_email}>"

    @classmethod
    @lru_cache(maxsize=None)
    def _load_template(cls, template_name: str) -> Template:
        template_path = cls.TEMPLATE_DIR / template_name
        return Template(template_path.read_text(encoding="utf-8"))

    def _render_template(self, template_name: str, context: dict[str, str | int]) -> str:
        normalized_context = {
            key: str(value)
            for key, value in context.items()
        }
        return self._load_template(template_name).safe_substitute(normalized_context)

    def _build_password_reset_otp_text(
        self,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int,
    ) -> str:
        return (
            f"Hello {recipient_name},\n\n"
            "We received a request to reset your password.\n\n"
            f"Your one-time password is: {otp_code}\n"
            f"It will expire in {expires_in_minutes} minutes.\n\n"
            "If you did not request this password reset, you can safely ignore this email.\n\n"
            f"Regards,\n{self.from_name}"
        )

    def _build_password_reset_otp_html(
        self,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int,
    ) -> str:
        return self._render_template(
            "password_reset_otp.html",
            {
                "current_year": datetime.now(timezone.utc).year,
                "expires_in_minutes": expires_in_minutes,
                "from_name": html.escape(self.from_name),
                "otp_code": html.escape(otp_code),
                "preheader": html.escape(
                    f"Your password reset OTP is {otp_code}. It expires in {expires_in_minutes} minutes."
                ),
                "recipient_name": html.escape(recipient_name),
            },
        )

    def _build_password_reset_otp_message(
        self,
        recipient_email: str,
        otp_code: str,
        expires_in_minutes: int,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        display_name = recipient_name or "there"
        message = EmailMessage()
        message["Subject"] = "Your password reset OTP"
        message["From"] = self._build_sender()
        message["To"] = recipient_email
        message.set_content(
            self._build_password_reset_otp_text(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            )
        )
        message.add_alternative(
            self._build_password_reset_otp_html(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            ),
            subtype="html",
        )
        return message

    def send_password_reset_otp(
        self,
        recipient_email: str,
        otp_code: str,
        expires_in_minutes: int,
        recipient_name: str | None = None,
    ) -> None:
        self._ensure_configured()
        message = self._build_password_reset_otp_message(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            otp_code=otp_code,
            expires_in_minutes=expires_in_minutes,
        )

        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.use_tls:
                smtp.starttls()

            if self.username:
                smtp.login(self.username, self.password)

            smtp.send_message(message)
