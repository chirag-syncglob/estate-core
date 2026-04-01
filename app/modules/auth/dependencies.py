from dataclasses import dataclass
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.settings import settings
from app.db.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.users.repository import UserRepository
from app.utils.email_util import EmailUtil
from app.utils.jwt_util import JwtUtil
from app.utils.otp_util import OtpUtil


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    role: str | None
    is_super_admin: bool


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


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_current_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    jwt_util: JwtUtil = Depends(get_jwt_util),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationException(
            message="Authentication credentials were not provided.",
            code="missing_authentication_credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_util.verify_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthenticationException(
            message="Invalid or expired access token.",
            code="invalid_access_token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    role = payload.get("role")
    normalized_role = str(role).strip().upper() if role is not None else None
    is_super_admin = bool(payload.get("is_super_admin")) or normalized_role == "SUPER_ADMIN"

    return AuthContext(
        user_id=user_id,
        role=normalized_role,
        is_super_admin=is_super_admin,
    )


def get_current_user_id(
    auth_context: AuthContext = Depends(get_current_auth_context),
) -> uuid.UUID:
    return auth_context.user_id


def require_roles(*roles: str, allow_super_admin: bool = True):
    normalized_roles = {
        role.strip().upper()
        for role in roles
        if role is not None and role.strip()
    }

    def dependency(
        auth_context: AuthContext = Depends(get_current_auth_context),
    ) -> AuthContext:
        if allow_super_admin and auth_context.is_super_admin:
            return auth_context

        if auth_context.role in normalized_roles:
            return auth_context

        raise AuthorizationException(
            message="You do not have permission to access this resource.",
            code="insufficient_role",
        )

    return dependency


def get_auth_service(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    jwt_util: JwtUtil = Depends(get_jwt_util),
    email_util: EmailUtil = Depends(get_email_util),
    otp_util: OtpUtil = Depends(get_otp_util),
):
    return AuthService(
        auth_repository=auth_repository,
        user_repository=user_repository,
        jwt_util=jwt_util,
        email_util=email_util,
        otp_util=otp_util,
        password_reset_otp_expire_minutes=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES,
    )
