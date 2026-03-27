from re import S

from dotenv import load_dotenv
import os


load_dotenv()

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
    
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{DATABASE_USER}:"
        f"{DATABASE_PASSWORD}@"
        f"{DATABASE_SERVER}:"
        f"{DATABASE_PORT}/"
        f"{DATABASE_NAME}"
    )
    
settings = Settings()