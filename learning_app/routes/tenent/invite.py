# routes/invite.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from database.db import get_session
from models.tenent.subscription_plan import Organization,InvitedUser, RoleEnum
from schemas.tenent.invited_user import InviteCreateSchema
import uuid
import os


router = APIRouter()

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "digidense.com")
FRONTEND_PROTOCOL = os.getenv("FRONTEND_PROTOCOL", "https")


# --------------------------------------------------
# Get tenant from subdomain
# --------------------------------------------------
async def get_tenant_from_request(request: Request, db: AsyncSession):

    host = request.headers.get("host")

    if not host:
        raise HTTPException(status_code=400, detail="Invalid host header")

    subdomain = host.split(".")[0]

    result = await db.execute(
        select(Organization).where(Organization.domain_name == subdomain)
    )

    tenant = result.scalars().first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant

# --------------------------------------------------
# Create Invite
# --------------------------------------------------
# @router.post("/invite", tags=["Invited user or Instructor"])
# from sqlalchemy import select
# from datetime import datetime, timedelta

@router.post("/invite", tags=["Invited user or Instructor"])
async def invite_user(
    organization_id: int,
    payload: InviteCreateSchema,
    db: AsyncSession = Depends(get_session),
):

    # 1️⃣ Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 2️⃣ Create invite
    expires_time = datetime.utcnow() + timedelta(hours=24)

    invite = InvitedUser(
        email=payload.email,
        name=payload.name,
        phone=payload.phone,
        role=payload.role,
        tenant_id=organization.id,
        expires_at=expires_time
    )

    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    # 3️⃣ Build URL
    # BASE_DOMAIN = "digidense.com"
    # org_url = f"https://{organization.domain_name}.{BASE_DOMAIN}"
    # register_url = f"{org_url}/register?token={invite.token}"
    
    BASE_DOMAIN = "digidense.com"
    ENV = os.getenv("ENV", "development")  # development or production

    if ENV == "production":
        org_url = f"https://{organization.domain_name}.{BASE_DOMAIN}"
    else:
    # LOCAL DEVELOPMENT
        org_url = f"http://{organization.domain_name}.localhost:5173"

        register_url = f"{org_url}/invite/register?token={invite.token}"

    # 4️⃣ SEND EMAIL (THIS WAS MISSING)
    send_invite_email(
        to_email=payload.email,
        org_name=organization.org_name,
        org_url=org_url,
        register_url=register_url
    )

    return {
        "message": "Invitation sent successfully",
        "register_url": register_url
    }
# --------------------------------------------------
# JWT Create Invite
# --------------------------------------------------
# from dependencies.auth_dep import get_current_user

# @router.post("/invite",tags=["Invited user or Instructor"])
# def invite_user(
#     payload: InviteCreateSchema,
#     db: Session = Depends(get_session),
#     # current_user: User = Depends(get_current_user)
#     current_user: Organization = Depends(get_current_user)
# ):
#     #1️⃣ Allow only admin
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Only admin can invite users")

#     # 2️⃣ Create invite
#     expires_time = datetime.utcnow() + timedelta(hours=24)

#     invite = InvitedUser(
#         email=payload.email,
#         name=payload.name,
#         phone=payload.phone,
#         role=payload.role,
#         tenant_id=current_user.tenant_id,   # 🔥 Important
#         expires_at=expires_time
#     )

#     db.add(invite)
#     db.commit()
#     db.refresh(invite)

#     # 3️⃣ Get tenant
#     tenant = db.query(Organization).filter(
#         Organization.id == current_user.tenant_id
#     ).first()

#     # 4️⃣ Build URL dynamically
#     BASE_DOMAIN = "digidense.com"

#     org_url = f"https://{tenant.subdomain}.{BASE_DOMAIN}"
#     register_url = f"{org_url}/register?token={invite.token}"

#     # 5️⃣ Send Email
#     send_invite_email(invite.email, tenant.name, org_url, register_url)

#     return {"message": "Invitation sent successfully"}

# --------------------------------------------------
# Gmail Sending Function
# --------------------------------------------------
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_invite_email(to_email, org_name, org_url, register_url):

    sender_email = "digidense.dev@gmail.com"
    app_password = "hzipfqwpmnxmjwwv"

    subject = f"Welcome to {org_name} Organization"

    html_content = f"""
    <h2>Welcome to {org_name} Organization</h2>
    <p>Your Organization URL:</p>
    <p><a href="{org_url}">{org_url}</a></p>
    <br>
    <p>Click below to complete registration:</p>
    <a href="{register_url}" 
       style="padding:10px 20px;
              background-color:#2563eb;
              color:white;
              text-decoration:none;
              border-radius:5px;">
        Complete Registration
    </a>
    <br><br>
    <p>If button doesn't work, copy this link:</p>
    <p>{register_url}</p>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email

    message.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, message.as_string())


# --------------------------------------------------
# Verify Invite Token
# --------------------------------------------------

@router.get("/invite/verify", tags=["Invited user or Instructor"])
async def verify_invite_token(
    token: str,
    db: AsyncSession = Depends(get_session)
):

    # 1️⃣ Find invite
    result = await db.execute(
        select(InvitedUser).where(InvitedUser.token == token)
    )

    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Invalid invitation token",
                "error_code": "INVALID_TOKEN"
            }
        )

    # 2️⃣ Check expiry
    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invitation link has expired",
                "error_code": "INVITE_EXPIRED"
            }
        )

    # 3️⃣ Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == invite.tenant_id)
    )

    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Organization not found",
                "error_code": "ORG_NOT_FOUND"
            }
        )

    # 4️⃣ Return invite details
    return {
        "valid": True,
        "email": invite.email,
        "name": invite.name,
        "phone": invite.phone,
        "role": invite.role,
        "organization": organization.org_name
    }