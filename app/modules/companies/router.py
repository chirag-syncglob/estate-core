import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import AuthContext, require_roles
from app.modules.companies.dependencies import get_company_service
from app.modules.companies.schema import CreateCompanySchema
from app.modules.companies.service import CompanyService


router = APIRouter()


@router.get("", dependencies=[Depends(require_roles("SUPER_ADMIN"))])
async def list_companies(company_service: CompanyService = Depends(get_company_service)):
    return company_service.list_companies()


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("SUPER_ADMIN"))])
async def create_company(
    data: CreateCompanySchema,
    company_service: CompanyService = Depends(get_company_service),
):
    return company_service.create_company(
        name=data.name,
        admin_name=data.admin_name,
        admin_email=data.admin_email,
    )


@router.get("/my-company")
async def get_my_company(
    company_service: CompanyService = Depends(get_company_service),
    auth_context: AuthContext = Depends(
        require_roles("COMPANY_ADMIN", allow_super_admin=False)
    ),
):
    return company_service.get_my_company(auth_context)


@router.get("/{company_id}", dependencies=[Depends(require_roles("SUPER_ADMIN"))])
async def get_company(
    company_id: uuid.UUID,
    company_service: CompanyService = Depends(get_company_service),
):
    return company_service.get_company(company_id)


@router.get("/users", dependencies=[Depends(require_roles("COMPANY_ADMIN", allow_super_admin=False))])
async def list_company_users(
    company_service: CompanyService = Depends(get_company_service),
    auth_context: AuthContext = Depends(require_roles("COMPANY_ADMIN", allow_super_admin=False)),
):
    return company_service.list_company_users(auth_context)