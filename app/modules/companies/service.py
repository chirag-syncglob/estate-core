from __future__ import annotations

import uuid

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.companies.repository import CompanyRepository
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


class CompanyService:
    def __init__(
        self,
        company_repository: CompanyRepository,
        user_repository: UserRepository,
        user_service: UserService,
    ):
        self.company_repository = company_repository
        self.user_repository = user_repository
        self.user_service = user_service

    @staticmethod
    def _build_company_response(company):
        admin = None
        if company.admin:
            admin = {
                "id": company.admin.id,
                "name": company.admin.name,
                "email": company.admin.email,
                "company_id": company.admin.company_id,
                "is_active": company.admin.is_active,
                "is_super_admin": company.admin.is_super_admin,
                "role": UserService._build_role_response(company.admin.role),
            }

        return {
            "id": company.id,
            "name": company.name,
            "admin_id": company.admin_id,
            "admin": admin,
        }

    def list_companies(self):
        companies = self.company_repository.list_companies()
        return [self._build_company_response(company) for company in companies]

    def get_company(self, company_id: uuid.UUID):
        company = self.company_repository.get_company_by_id(company_id)
        if not company:
            raise NotFoundException(
                message="Company not found.",
                code="company_not_found",
            )

        return self._build_company_response(company)

    def create_company(
        self,
        name: str,
        admin_name: str,
        admin_email: str,
    ):
        existing_company = self.company_repository.get_company_by_name(name)
        if existing_company:
            raise ConflictException(
                message="A company with this name already exists.",
                code="company_already_exists",
            )

        existing_user = self.user_repository.get_user_by_email(admin_email)
        if existing_user:
            raise ConflictException(
                message="A user with this email already exists.",
                code="user_already_exists",
            )

        company = self.company_repository.create_company(name=name)
        admin_user = self.user_service.create_company_admin(
            company_id=company.id,
            name=admin_name,
            email=admin_email,
            send_invite=False,
        )
        company = self.company_repository.update_company(
            company_id=company.id,
            admin_id=admin_user.id,
        )
        self.user_service.send_account_setup_otp(admin_user)
        return self._build_company_response(company)
