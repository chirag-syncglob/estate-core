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

    def _build_otp_html(
        self,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int,
        *,
        page_title: str,
        header_eyebrow: str,
        header_title: str,
        intro_text: str,
        outro_text: str,
        preheader: str,
    ) -> str:
        return self._render_template(
            "password_reset_otp.html",
            {
                "current_year": datetime.now(timezone.utc).year,
                "expires_in_minutes": expires_in_minutes,
                "from_name": html.escape(self.from_name),
                "header_eyebrow": html.escape(header_eyebrow),
                "header_title": html.escape(header_title),
                "intro_text": html.escape(intro_text),
                "otp_code": html.escape(otp_code),
                "outro_text": html.escape(outro_text),
                "page_title": html.escape(page_title),
                "preheader": html.escape(preheader),
                "recipient_name": html.escape(recipient_name),
            },
        )

    def _build_otp_message(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._build_sender()
        message["To"] = recipient_email
        message.set_content(text_content)
        message.add_alternative(html_content, subtype="html")
        return message

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
        return self._build_otp_html(
            recipient_name=recipient_name,
            otp_code=otp_code,
            expires_in_minutes=expires_in_minutes,
            page_title="Password Reset OTP",
            header_eyebrow="Password Reset Verification",
            header_title="Your OTP is ready",
            intro_text=(
                "We received a request to reset your password. "
                "Use the one-time password below to continue securely."
            ),
            outro_text=(
                "If you did not request this password reset, you can safely ignore this email. "
                "Your account will remain unchanged."
            ),
            preheader=(
                f"Your password reset OTP is {otp_code}. "
                f"It expires in {expires_in_minutes} minutes."
            ),
        )

    def _build_password_reset_otp_message(
        self,
        recipient_email: str,
        otp_code: str,
        expires_in_minutes: int,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        display_name = recipient_name or "there"
        return self._build_otp_message(
            recipient_email=recipient_email,
            recipient_name=display_name,
            subject="Your password reset OTP",
            text_content=self._build_password_reset_otp_text(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            ),
            html_content=self._build_password_reset_otp_html(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            ),
        )

    def _build_account_setup_otp_text(
        self,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int,
    ) -> str:
        return (
            f"Hello {recipient_name},\n\n"
            "An administrator created your Estate Core account.\n\n"
            f"Your one-time password is: {otp_code}\n"
            f"It will expire in {expires_in_minutes} minutes.\n\n"
            "Use this OTP to set your password and activate your account.\n\n"
            "If you were not expecting this invitation, please contact your administrator.\n\n"
            f"Regards,\n{self.from_name}"
        )

    def _build_account_setup_otp_html(
        self,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int,
    ) -> str:
        return self._build_otp_html(
            recipient_name=recipient_name,
            otp_code=otp_code,
            expires_in_minutes=expires_in_minutes,
            page_title="Account Setup OTP",
            header_eyebrow="Account Setup Verification",
            header_title="Set your password",
            intro_text=(
                "An administrator created your account. "
                "Use the one-time password below to set your password and activate your account securely."
            ),
            outro_text=(
                "If you were not expecting this invitation, please contact your administrator before proceeding."
            ),
            preheader=(
                f"Your account setup OTP is {otp_code}. "
                f"It expires in {expires_in_minutes} minutes."
            ),
        )

    def _build_account_setup_otp_message(
        self,
        recipient_email: str,
        otp_code: str,
        expires_in_minutes: int,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        display_name = recipient_name or "there"
        return self._build_otp_message(
            recipient_email=recipient_email,
            recipient_name=display_name,
            subject="Set up your Estate Core account",
            text_content=self._build_account_setup_otp_text(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            ),
            html_content=self._build_account_setup_otp_html(
                recipient_name=display_name,
                otp_code=otp_code,
                expires_in_minutes=expires_in_minutes,
            ),
        )

    def _send_message(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.use_tls:
                smtp.starttls()

            if self.username:
                smtp.login(self.username, self.password)

            smtp.send_message(message)

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
        self._send_message(message)

    def send_account_setup_otp(
        self,
        recipient_email: str,
        otp_code: str,
        expires_in_minutes: int,
        recipient_name: str | None = None,
    ) -> None:
        self._ensure_configured()
        message = self._build_account_setup_otp_message(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            otp_code=otp_code,
            expires_in_minutes=expires_in_minutes,
        )
        self._send_message(message)
