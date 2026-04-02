import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import require_roles
from app.modules.companies.dependencies import get_company_service
from app.modules.companies.schema import CreateCompanySchema
from app.modules.companies.service import CompanyService


router = APIRouter(dependencies=[Depends(require_roles("SUPER_ADMIN"))])


@router.get("")
async def list_companies(company_service: CompanyService = Depends(get_company_service)):
    return company_service.list_companies()


@router.get("/{company_id}")
async def get_company(
    company_id: uuid.UUID,
    company_service: CompanyService = Depends(get_company_service),
):
    return company_service.get_company(company_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CreateCompanySchema,
    company_service: CompanyService = Depends(get_company_service),
):
    return company_service.create_company(
        name=data.name,
        admin_name=data.admin_name,
        admin_email=data.admin_email,
    )
