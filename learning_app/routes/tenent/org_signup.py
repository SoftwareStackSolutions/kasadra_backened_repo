from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

from database.db import get_session
from core.jwt_utils import create_access_token
from models.tenent.subscription_plan import Organization

router = APIRouter(prefix="/tenant", tags=["Tenant Signup"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BASE_DOMAIN = os.getenv("BASE_DOMAIN")
ENV = os.getenv("ENV")


class TenantSignupRequest(BaseModel):
    org_name: str
    email: EmailStr
    domain_name: str
    password: str
    subscription_id: int


@router.post("/signup")
async def tenant_signup(payload: TenantSignupRequest,
                        session: AsyncSession = Depends(get_session)):

    domain = payload.domain_name.lower().strip()
    email = payload.email.lower().strip()

    site_url = (
        f"http://{domain}.{BASE_DOMAIN}"
        if ENV == "development"
        else f"https://{domain}.{BASE_DOMAIN}"
    )

    password_hash = pwd_context.hash(payload.password)

    org = Organization(
        org_name=payload.org_name,
        email=email,
        domain_name=domain,
        site_url=site_url,
        password_hash=password_hash,
        subscription_id=payload.subscription_id
    )

    session.add(org)
    await session.commit()
    await session.refresh(org)

    # Generate JWT for frontend
    access_token = create_access_token({
        "org_id": org.id,
        "domain": org.domain_name,
        "email": org.email
    })

    return {
        "org_id": org.id,
        "org_name": org.org_name,
        "email": org.email,
        "domain_name": org.domain_name,
        "subscription_id": org.subscription_id,
        "site_url": org.site_url,
        "access_token": access_token,
        "message": "Signup successful"
    }