import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationException
from app.core.settings import settings
from app.db.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.utils.email_util import EmailUtil
from app.utils.jwt_util import JwtUtil
from app.utils.otp_util import OtpUtil


bearer_scheme = HTTPBearer(auto_error=False)


def get_jwt_util() -> JwtUtil:
    return JwtUtil(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE
    )
    

def get_email_util() -> EmailUtil:
    return EmailUtil(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.SMTP_FROM_NAME,
        use_tls=settings.SMTP_USE_TLS,
    )


def get_otp_util() -> OtpUtil:
    return OtpUtil(secret_key=settings.OTP_SECRET_KEY)


def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    jwt_util: JwtUtil = Depends(get_jwt_util),
) -> uuid.UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationException(
            message="Authentication credentials were not provided.",
            code="missing_authentication_credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_util.verify_access_token(credentials.credentials)
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthenticationException(
            message="Invalid or expired access token.",
            code="invalid_access_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_auth_service(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    jwt_util: JwtUtil = Depends(get_jwt_util),
    email_util: EmailUtil = Depends(get_email_util),
    otp_util: OtpUtil = Depends(get_otp_util),
):
    return AuthService(
        auth_repository=auth_repository,
        jwt_util=jwt_util,
        email_util=email_util,
        otp_util=otp_util,
        password_reset_otp_expire_minutes=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES,
    )
