from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import os

from database.db import get_session
from models.tenent.subscription_plan import Organization

router = APIRouter(prefix="/tenant", tags=["Tenant Signup"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Read base domain from env
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "digidense.com")


# =====================
# Request Schema
# =====================
class TenantSignupRequest(BaseModel):
    org_name: str = Field(..., min_length=3)
    domain_name: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    subscription_id: int


# =====================
# Helpers
# =====================
def validate_domain(domain: str) -> bool:
    return domain.isalnum() and len(domain) >= 3


# =====================
# API
# =====================
@router.post("/signup")
async def tenant_signup(
    payload: TenantSignupRequest,
    session: AsyncSession = Depends(get_session)
):
    domain = payload.domain_name.lower().strip()

    if not validate_domain(domain):
        raise HTTPException(status_code=400, detail="Invalid domain name")

    # Check if domain already exists
    result = await session.execute(
        select(Organization).where(Organization.domain_name == domain)
    )
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Domain already exists")

    # Build tenant URL
    site_url = f"https://{domain}.{BASE_DOMAIN}"

    password_hash = pwd_context.hash(payload.password)

    org = Organization(
        org_name=payload.org_name,
        domain_name=domain,
        site_url=site_url,
        password_hash=password_hash,
        subscription_id=payload.subscription_id
    )

    session.add(org)
    await session.commit()
    await session.refresh(org)

    return {
        "org_id": org.id,
        "org_name": org.org_name,
        "domain_name": org.domain_name,
        "subscription_id": org.subscription_id,
        "site_url": org.site_url
    }