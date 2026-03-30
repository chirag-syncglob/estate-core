from __future__ import annotations

import hashlib
import hmac
import secrets
import string


class OtpUtil:
    def __init__(self, secret_key: str, length: int = 6) -> None:
        if not secret_key:
            raise ValueError("secret_key is required")
        if length <= 0:
            raise ValueError("length must be greater than 0")

        self.secret_key = secret_key
        self.length = length

    def generate_otp(self) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(self.length))

    def hash_otp(self, otp_code: str) -> str:
        if not otp_code:
            raise ValueError("otp_code is required")

        return hmac.new(
            self.secret_key.encode("utf-8"),
            otp_code.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
