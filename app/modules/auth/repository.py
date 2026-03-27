from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, DatabaseException
from app.db.models import User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, name: str, email: str, hashed_password: str, is_super_admin: bool = False):
        try:
            new_user = User(
                name=name,
                email=email,
                password_hash=hashed_password,
                is_super_admin=is_super_admin,
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A user with this email already exists.",
                code="user_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to create the user right now.") from exc

    def get_user_by_email(self, email: str):
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the user right now.") from exc
