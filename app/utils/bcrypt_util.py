import bcrypt


class BcryptUtil:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain password using bcrypt.
        """
        if not password:
            raise ValueError("Password cannot be empty")

        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)

        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        """
        if not password or not hashed_password:
            return False

        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def needs_rehash(hashed_password: str, rounds: int = 12) -> bool:
        """
        Check if hash needs upgrade (e.g., rounds changed).
        """
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(b"", hashed_bytes) and bcrypt.gensalt(rounds) != hashed_bytes[:29]