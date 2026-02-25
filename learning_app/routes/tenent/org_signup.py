# # routes/tenant/auth.py

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr
# from database.db import get_session
# from core.jwt_utils import create_access_token
# from models.tenent.subscription_plan import Organization
# from core.security import create_access_token

# router = APIRouter(prefix="/tenant", tags=["Tenant Auth"])
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# # -------------------------------
# # Request Schemas
# # -------------------------------

# class TenantSignupRequest(BaseModel):
#     org_name: str
#     email: EmailStr
#     domain_name: str
#     password: str
#     subscription_id: int


# class TenantLoginRequest(BaseModel):
#     email: EmailStr
#     password: str

# # -------------------------------
# # Signup
# # -------------------------------

# @router.post("/signup", status_code=status.HTTP_201_CREATED)
# async def tenant_signup(
#     payload: TenantSignupRequest,
#     session: AsyncSession = Depends(get_session)
# ):
#     email = payload.email.lower().strip()
#     domain = payload.domain_name.lower().strip()

#     # Check duplicate email
#     existing_email = await session.execute(
#         select(Organization).where(Organization.email == email)
#     )
#     if existing_email.scalar_one_or_none():
#         raise HTTPException(
#             status_code=400,
#             detail="Email already registered"
#         )

#     # Check duplicate domain
#     existing_domain = await session.execute(
#         select(Organization).where(Organization.domain_name == domain)
#     )
#     if existing_domain.scalar_one_or_none():
#         raise HTTPException(
#             status_code=400,
#             detail="Domain already taken"
#         )

#     # Hash password
#     password_hash = pwd_context.hash(payload.password)

#     # Create organization
#     org = Organization(
#         org_name=payload.org_name,
#         email=email,
#         domain_name=domain,
#         site_url=f"http://{domain}.localhost",
#         password_hash=password_hash,
#         subscription_id=payload.subscription_id
#     )

#     session.add(org)
#     await session.commit()
#     await session.refresh(org)

#     #  Generate JWT
#     access_token = create_access_token({
#         "org_id": org.id,
#         "domain": org.domain_name,
#         "email": org.email,
#         "first_login": True
#     })

#     return {
#         "org_id": org.id,
#         "org_name": org.org_name,
#         "email": org.email,
#         "domain_name": org.domain_name,
#         "subscription_id": org.subscription_id,
#         "site_url": org.site_url,
#         "access_token": access_token,
#         "message": "Signup successful"
#     }


# # -------------------------------
# # Login
# # -------------------------------

# @router.post("/login")
# async def tenant_login(
#     payload: TenantLoginRequest,
#     session: AsyncSession = Depends(get_session)
# ):
#     email = payload.email.lower().strip()

#     result = await session.execute(
#         select(Organization).where(Organization.email == email)
#     )
#     org = result.scalar_one_or_none()

#     if not org:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )

#     if not pwd_context.verify(payload.password, org.password_hash):
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid credentials"
#         )

#     access_token = create_access_token({
#         "org_id": org.id,
#         "domain": org.domain_name,
#         "email": org.email,
#         "first_login": False
#     })

#     return {
#         "org_id": org.id,
#         "domain_name": org.domain_name,
#         "email": org.email,
#         "org_name": org.org_name,
#         "site_url": org.site_url,
#         "access_token": access_token,
#         "message": "Login successful"
#     }

# routes/tenant/auth.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from database.db import get_session
from models.tenent.subscription_plan import Organization
from core.security import create_access_token

# Load environment variable
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")

router = APIRouter(prefix="/tenant", tags=["Tenant Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------------
# Request Schemas
# -------------------------------

class TenantSignupRequest(BaseModel):
    org_name: str
    email: EmailStr
    domain_name: str
    password: str
    subscription_id: int


class TenantLoginRequest(BaseModel):
    email: EmailStr
    password: str


# -------------------------------
# Signup
# -------------------------------

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def tenant_signup(
    payload: TenantSignupRequest,
    session: AsyncSession = Depends(get_session)
):
    email = payload.email.lower().strip()
    domain = payload.domain_name.lower().strip()

    # Check duplicate email
    existing_email = await session.execute(
        select(Organization).where(Organization.email == email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check duplicate domain
    existing_domain = await session.execute(
        select(Organization).where(Organization.domain_name == domain)
    )
    if existing_domain.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Domain already taken"
        )

    # Hash password
    password_hash = pwd_context.hash(payload.password)

    # Determine protocol automatically
    PROTOCOL = "http" if BASE_DOMAIN == "localhost" else "https"

    # Build site URL dynamically
    site_url = f"{PROTOCOL}://{domain}.{BASE_DOMAIN}"

    # Create organization
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

    # Generate JWT
    access_token = create_access_token({
        "org_id": org.id,
        "domain": org.domain_name,
        "email": org.email,
        "first_login": True
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


# -------------------------------
# Login
# -------------------------------

@router.post("/login")
async def tenant_login(
    payload: TenantLoginRequest,
    session: AsyncSession = Depends(get_session)
):
    email = payload.email.lower().strip()

    result = await session.execute(
        select(Organization).where(Organization.email == email)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not pwd_context.verify(payload.password, org.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token({
        "org_id": org.id,
        "domain": org.domain_name,
        "email": org.email,
        "first_login": False
    })

    return {
        "org_id": org.id,
        "domain_name": org.domain_name,
        "site_url": org.site_url,
        "access_token": access_token,
        "message": "Login successful"
    }