from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictException, DatabaseException
from app.db.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        name: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_super_admin: bool = False,
        role_id: uuid.UUID | None = None,
    ):
        try:
            new_user = User(
                name=name,
                email=email,
                password_hash=hashed_password,
                is_active=is_active,
                is_super_admin=is_super_admin,
                role_id=role_id,
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
            return (
                self.db.query(User)
                .options(joinedload(User.role))
                .filter(User.email == email)
                .first()
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the user right now.") from exc

    def get_user_by_id(self, user_id: uuid.UUID):
        try:
            return (
                self.db.query(User)
                .options(joinedload(User.role))
                .filter(User.id == user_id)
                .first()
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the user right now.") from exc

    def get_all_users(self):
        try:
            return self.db.query(User).options(joinedload(User.role)).all()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load users right now.") from exc

    def update_user(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        hashed_password: str | None = None,
        role_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        is_super_admin: bool | None = None,
    ):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ConflictException(
                    message="User not found.",
                    code="user_not_found",
                )

            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if hashed_password is not None:
                user.password_hash = hashed_password
            if role_id is not None:
                user.role_id = role_id
            if is_active is not None:
                user.is_active = is_active
            if is_super_admin is not None:
                user.is_super_admin = is_super_admin

            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A user with this email already exists.",
                code="user_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to update the user right now.") from exc
