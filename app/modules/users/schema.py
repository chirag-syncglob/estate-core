from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role_id: UUID
    company_id: UUID | None = None


class UpdateUserSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    role_id: UUID | None = None
    is_active: bool | None = None
