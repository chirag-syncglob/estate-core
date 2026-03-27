from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from jose import JWTError, ExpiredSignatureError, jwt


class JwtUtil:
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
    ) -> None:
        if not secret_key:
            raise ValueError("secret_key is required")
        if access_token_expire_minutes <= 0:
            raise ValueError("access_token_expire_minutes must be greater than 0")
        if refresh_token_expire_days <= 0:
            raise ValueError("refresh_token_expire_days must be greater than 0")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        self.audience = audience

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _build_payload(
        self,
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = self._now()
        expire_at = now + expires_delta

        payload: Dict[str, Any] = {
            "sub": str(subject),
            "type": token_type,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expire_at.timestamp()),
            "jti": str(uuid4()),
        }

        if self.issuer:
            payload["iss"] = self.issuer

        if self.audience:
            payload["aud"] = self.audience

        if extra_claims:
            payload.update(extra_claims)

        return payload

    def _encode(self, payload: Dict[str, Any]) -> str:
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(
        self,
        subject: str,
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_minutes: Optional[int] = None,
    ) -> str:
        minutes = expires_minutes or self.access_token_expire_minutes
        payload = self._build_payload(
            subject=subject,
            token_type=self.ACCESS_TOKEN_TYPE,
            expires_delta=timedelta(minutes=minutes),
            extra_claims=extra_claims,
        )
        return self._encode(payload)

    def create_refresh_token(
        self,
        subject: str,
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_days: Optional[int] = None,
    ) -> str:
        days = expires_days or self.refresh_token_expire_days
        payload = self._build_payload(
            subject=subject,
            token_type=self.REFRESH_TOKEN_TYPE,
            expires_delta=timedelta(days=days),
            extra_claims=extra_claims,
        )
        return self._encode(payload)

    def create_token_pair(
        self,
        subject: str,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        access_token = self.create_access_token(
            subject=subject,
            extra_claims=extra_claims,
        )
        refresh_token = self.create_refresh_token(
            subject=subject,
            extra_claims=extra_claims,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "access_token_expires_in": self.access_token_expire_minutes * 60,
            "refresh_token_expires_in": self.refresh_token_expire_days * 24 * 60 * 60,
        }

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            options = {
                "verify_aud": self.audience is not None,
            }

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options=options,
            )

            return payload

        except ExpiredSignatureError as exc:
            raise ValueError("Token has expired") from exc
        except JWTError as exc:
            raise ValueError("Invalid token") from exc

    def get_subject(self, token: str) -> str:
        payload = self.decode_token(token)
        subject = payload.get("sub")

        if not subject:
            raise ValueError("Token subject is missing")

        return str(subject)

    def get_token_type(self, token: str) -> str:
        payload = self.decode_token(token)
        token_type = payload.get("type")

        if token_type not in {self.ACCESS_TOKEN_TYPE, self.REFRESH_TOKEN_TYPE}:
            raise ValueError("Invalid token type")

        return str(token_type)

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        payload = self.decode_token(token)

        if payload.get("type") != self.ACCESS_TOKEN_TYPE:
            raise ValueError("Provided token is not an access token")

        if not payload.get("sub"):
            raise ValueError("Access token subject is missing")

        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        payload = self.decode_token(token)

        if payload.get("type") != self.REFRESH_TOKEN_TYPE:
            raise ValueError("Provided token is not a refresh token")

        if not payload.get("sub"):
            raise ValueError("Refresh token subject is missing")

        return payload

    def refresh_access_token(
        self,
        refresh_token: str,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = self.verify_refresh_token(refresh_token)
        subject = str(payload["sub"])

        new_access_token = self.create_access_token(
            subject=subject,
            extra_claims=extra_claims,
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "access_token_expires_in": self.access_token_expire_minutes * 60,
        }

    def refresh_token_pair(
        self,
        refresh_token: str,
        extra_claims: Optional[Dict[str, Any]] = None,
        rotate_refresh_token: bool = True,
    ) -> Dict[str, Any]:
        payload = self.verify_refresh_token(refresh_token)
        subject = str(payload["sub"])

        access_token = self.create_access_token(
            subject=subject,
            extra_claims=extra_claims,
        )

        response: Dict[str, Any] = {
            "access_token": access_token,
            "token_type": "bearer",
            "access_token_expires_in": self.access_token_expire_minutes * 60,
        }

        if rotate_refresh_token:
            new_refresh_token = self.create_refresh_token(
                subject=subject,
                extra_claims=extra_claims,
            )
            response["refresh_token"] = new_refresh_token
            response["refresh_token_expires_in"] = self.refresh_token_expire_days * 24 * 60 * 60

        return response