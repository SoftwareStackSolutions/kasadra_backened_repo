from pydantic import BaseModel, EmailStr
from typing import Optional
from models.tenent.invited import RoleEnum


class InviteCreateSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    role: RoleEnum

class InviteRegisterSchema(BaseModel):
    token: str
    name: str
    phone: str
    password: str