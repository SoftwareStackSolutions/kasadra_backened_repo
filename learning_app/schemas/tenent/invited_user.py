from pydantic import BaseModel, EmailStr
from typing import Optional
from models.tenent.subscription_plan import RoleEnum


class InviteCreateSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    role: RoleEnum