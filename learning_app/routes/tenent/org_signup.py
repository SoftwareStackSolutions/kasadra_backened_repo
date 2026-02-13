from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
import os

from core.security import create_access_token
from database.db import get_session
from models.tenent.subscription_plan import Organization

router = APIRouter(prefix="/tenant", tags=["Tenant Signup"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "digidense.com")


# =====================
# Request Schema
# =====================
class TenantSignupRequest(BaseModel):
    org_name: str = Field(..., min_length=3)
    email: EmailStr
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
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    domain = payload.domain_name.lower().strip()
    email = payload.email.lower().strip()

    if not validate_domain(domain):
        raise HTTPException(status_code=400, detail="Invalid domain name")

    # Check domain
    domain_check = await session.execute(
        select(Organization).where(Organization.domain_name == domain)
    )
    if domain_check.scalars().first():
        raise HTTPException(status_code=409, detail="Domain already exists")

    # Check email
    email_check = await session.execute(
        select(Organization).where(Organization.email == email)
    )
    if email_check.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

    site_url = f"https://{domain}.{BASE_DOMAIN}"

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

    # 🔐 Create JWT
    access_token = create_access_token(
        data={
            "org_id": org.id,
            "domain": org.domain_name,
            "email": org.email
        }
    )

    # ✅ Set Cookie (IMPORTANT PART)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,   # ⚠ set True in production (HTTPS)
        samesite="lax", # use "none" for cross-domain HTTPS
        max_age=60 * 60 * 5  # 5 hours
    )

    return {
        "org_id": org.id,
        "org_name": org.org_name,
        "email": org.email,
        "domain_name": org.domain_name,
        "subscription_id": org.subscription_id,
        "site_url": org.site_url,
        "message": "Signup successful"
    }
