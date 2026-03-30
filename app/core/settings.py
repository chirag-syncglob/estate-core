import os

from dotenv import load_dotenv


load_dotenv()


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # Database configuration
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_SERVER = os.getenv("DATABASE_SERVER", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    
    # Super admin credentials
    SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL")
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")
    
    #JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ISSUER = os.getenv("JWT_ISSUER")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")

    # Password reset configuration
    PASSWORD_RESET_OTP_EXPIRE_MINUTES = int(
        os.getenv("PASSWORD_RESET_OTP_EXPIRE_MINUTES", "10")
    )
    OTP_SECRET_KEY = os.getenv("OTP_SECRET_KEY", JWT_SECRET_KEY)

    # SMTP configuration
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Estate Core")
    SMTP_USE_TLS = _get_bool_env("SMTP_USE_TLS", default=True)
    
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{DATABASE_USER}:"
        f"{DATABASE_PASSWORD}@"
        f"{DATABASE_SERVER}:"
        f"{DATABASE_PORT}/"
        f"{DATABASE_NAME}"
    )
    
settings = Settings()