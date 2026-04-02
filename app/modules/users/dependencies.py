from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.modules.auth.dependencies import get_auth_repository, get_email_util, get_otp_util
from app.modules.auth.repository import AuthRepository
from app.db.session import get_db
from app.modules.roles.dependencies import get_role_repository
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService
from app.utils.email_util import EmailUtil
from app.utils.otp_util import OtpUtil


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    auth_repository: AuthRepository = Depends(get_auth_repository),
    email_util: EmailUtil = Depends(get_email_util),
    otp_util: OtpUtil = Depends(get_otp_util),
) -> UserService:
    return UserService(
        user_repository=user_repository,
        role_repository=role_repository,
        auth_repository=auth_repository,
        email_util=email_util,
        otp_util=otp_util,
        password_reset_otp_expire_minutes=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES,
    )
