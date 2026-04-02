from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictException, DatabaseException, NotFoundException
from app.db.models import Company, User


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_companies(self):
        try:
            return (
                self.db.query(Company)
                .options(joinedload(Company.admin).joinedload(User.role))
                .order_by(Company.name.asc())
                .all()
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load companies right now.") from exc

    def get_company_by_id(self, company_id: uuid.UUID):
        try:
            return (
                self.db.query(Company)
                .options(joinedload(Company.admin).joinedload(User.role))
                .filter(Company.id == company_id)
                .first()
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the company right now.") from exc

    def get_company_by_name(self, name: str):
        try:
            return self.db.query(Company).filter(Company.name == name).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load the company right now.") from exc

    def create_company(self, name: str, admin_id: uuid.UUID | None = None):
        try:
            company = Company(name=name, admin_id=admin_id)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A company with this name already exists.",
                code="company_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to create company right now.") from exc

    def update_company(
        self,
        company_id: uuid.UUID,
        name: str | None = None,
        admin_id: uuid.UUID | None = None,
    ):
        try:
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise NotFoundException(
                    message="Company not found.",
                    code="company_not_found",
                )

            if name is not None:
                company.name = name
            if admin_id is not None:
                company.admin_id = admin_id

            self.db.commit()
            self.db.refresh(company)
            return self.get_company_by_id(company.id)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                message="A company with this name already exists.",
                code="company_already_exists",
            ) from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to update the company right now.") from exc
