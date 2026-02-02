from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_session
from models.tenent.email_otp import EmailOTP
from schemas.tenent.auth import SendOTPRequest, VerifyOTPRequest
from utils.tenent.otp import generate_otp, hash_otp
from utils.tenent.email import send_otp_email
from utils.tenent.jwt import create_access_token
from sqlalchemy import delete

router = APIRouter(tags=["Gmail-OTP"])

@router.post("/send-otp")
async def send_otp(data: SendOTPRequest, db: AsyncSession = Depends(get_session)):
    otp = generate_otp()

    # remove any previous OTP for this email
    await db.execute(
        delete(EmailOTP).where(EmailOTP.email == data.email)
    )
    await db.commit()

    record = EmailOTP(
        email=data.email,
        otp_hash=hash_otp(otp)
    )
    db.add(record)
    await db.commit()

    send_otp_email(data.email, otp)

    return {
        "message": "OTP sent for email verification"
    }


from sqlalchemy import delete

@router.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(EmailOTP).where(EmailOTP.email == data.email)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=400, detail="OTP not found")

    if record.otp_hash != hash_otp(data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # delete OTP after success
    await db.execute(
        delete(EmailOTP).where(EmailOTP.email == data.email)
    )
    await db.commit()

    return {
        "message": "Email is valid and verified"
    }



# from fastapi import HTTPException
# from sqlalchemy import select, delete

# @router.post("/send-otp")
# async def send_otp(
#     data: SendOTPRequest,
#     db: AsyncSession = Depends(get_session)
# ):
#     # 1. Check if OTP already exists for this email
#     result = await db.execute(
#         select(EmailOTP).where(EmailOTP.email == data.email)
#     )
#     existing_otp = result.scalar_one_or_none()

#     if existing_otp:
#         raise HTTPException(
#             status_code=200,
#             detail="Email already exists , please enter new gmail"
#         )

#     # 2. Generate OTP
#     otp = generate_otp()

#     # 3. Save OTP (hashed)
#     record = EmailOTP(
#         email=data.email,
#         otp_hash=hash_otp(otp)
#     )
#     db.add(record)
#     await db.commit()

#     # 4. Send OTP email
#     send_otp_email(data.email, otp)

#     return {
#         "message": "OTP sent for email verification"
#     }


