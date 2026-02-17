from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

from core.security import create_access_token
from database.db import get_session
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
async def tenant_signup(
    payload: TenantSignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
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

    # 🔐 Create JWT
    access_token = create_access_token({
        "org_id": org.id,
        "domain": org.domain_name,
        "email": org.email
    })

    # -------------------------
    # COOKIE CONFIG
    # -------------------------
    if ENV == "production":
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,               # HTTPS required
            samesite="none",
            domain=f".{BASE_DOMAIN}",  # .digidense.com
            max_age=60 * 60 * 5,
            path="/"
        )
    else:
        # LOCAL (NO domain!)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 5,
            path="/"
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
