from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.utils.jwt_util import JwtUtil


def get_jwt_util() -> JwtUtil:
    return JwtUtil(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE
    )
    

def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)


def get_auth_service(auth_repository: AuthRepository = Depends(get_auth_repository), jwt_util: JwtUtil = Depends(get_jwt_util)):
    return AuthService(auth_repository, jwt_util)