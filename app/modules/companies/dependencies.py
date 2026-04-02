from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.service import CompanyService
from app.modules.users.dependencies import get_user_repository, get_user_service
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


def get_company_repository(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_company_service(
    company_repository: CompanyRepository = Depends(get_company_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    user_service: UserService = Depends(get_user_service),
) -> CompanyService:
    return CompanyService(
        company_repository=company_repository,
        user_repository=user_repository,
        user_service=user_service,
    )
