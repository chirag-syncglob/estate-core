from app.core.exceptions import AuthenticationException
from app.modules.auth.repository import AuthRepository
from app.utils.bcrypt_util import BcryptUtil
from app.utils.jwt_util import JwtUtil


class AuthService:
    def __init__(self, auth_repository: AuthRepository, jwt_util: JwtUtil):
        self.auth_repository = auth_repository
        self.jwt_util = jwt_util

    def login(self, email: str, password: str):
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            raise AuthenticationException(
                message="Invalid email or password.",
                code="invalid_credentials",
            )

        is_valid_password = BcryptUtil.verify_password(password, user.password_hash)
        if not is_valid_password:
            raise AuthenticationException(
                message="Invalid email or password.",
                code="invalid_credentials",
            )

        token_pair = self.jwt_util.create_token_pair(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin},
        )

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_active": user.is_active,
                "is_super_admin": user.is_super_admin,
            },
            "tokens": token_pair,
        }

    def register(self, username: str, email: str, password: str):
        hashed_password = BcryptUtil.hash_password(password)
        user = self.auth_repository.create_user(
            name=username,
            email=email,
            hashed_password=hashed_password,
        )
        token_pair = self.jwt_util.create_token_pair(
            subject=str(user.id),
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin},
        )

        return {
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_active": user.is_active,
                "is_super_admin": user.is_super_admin,
            },
            "tokens": token_pair,
        }
