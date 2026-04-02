from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateCompanySchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    admin_name: str = Field(min_length=1, max_length=255)
    admin_email: EmailStr
