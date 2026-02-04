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
from datetime import datetime, timedelta
from sqlalchemy import delete, select
from database.dbconfig import OTP_EXPIRY_MINUTES, MAX_RESEND_ATTEMPTS

router = APIRouter(tags=["Gmail-OTP"])

#######################################################
# ✅ SEND OTP (First time)
#######################################################

from datetime import datetime, timedelta
from sqlalchemy import delete, select

@router.post("/send-otp")
async def send_otp(
    data: SendOTPRequest,
    db: AsyncSession = Depends(get_session)
):
#     # 1. Check if OTP already exists for this email
    result = await db.execute(
        select(EmailOTP).where(EmailOTP.email == data.email)
    )
    existing_otp = result.scalar_one_or_none()

    if existing_otp:
        raise HTTPException(
            status_code=200,
            detail={
                "message": "Email already exists , please enter new gmail",
                "error_code": "EMAIL_ALREADY_EXISTS"
            }
        )

    # 2️⃣ DELETE EXPIRED OTPS
    await db.execute(
        delete(EmailOTP).where(EmailOTP.expires_at < datetime.utcnow())
    )
    await db.commit()

    # 3️⃣ CHECK EXISTING OTP
    otp_result = await db.execute(
        select(EmailOTP).where(EmailOTP.email == data.email)
    )
    existing_otp = otp_result.scalar_one_or_none()

    if existing_otp:
        raise HTTPException(
            status_code=400,
            detail={
                "message":"OTP already sent. Please verify or wait for expiry.",
                "error_code": "OTP_ALREADY_USED"
            }
        )

    # 4️⃣ GENERATE & SEND OTP
    otp = generate_otp()

    record = EmailOTP(
        email=data.email,
        otp_hash=hash_otp(otp),
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        resend_count=0
    )

    db.add(record)
    await db.commit()

    send_otp_email(data.email, otp)

    return {"message": "OTP sent successfully"}


#######################################################
# ✅ RESEND OTP (AFTER EXPIRY ONLY)
#######################################################
@router.post("/resend-otp")
async def resend_otp(
    data: SendOTPRequest,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(EmailOTP).where(EmailOTP.email == data.email)
    )
    record = result.scalar_one_or_none()

    # 1️⃣ OTP NEVER REQUESTED
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "OTP not requested yet. Please request OTP first.",
                "error_code":"OTP_INVALID"
            }
        )

    # 2️⃣ OTP STILL VALID
    if record.expires_at > datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail={
                 "message":"OTP already sent and still valid. Please wait before resending.",
                 "error_code":"OTP_RESEND_TOO_SOON"
            }
        )

    # 3️⃣ RESEND LIMIT
    if record.resend_count >= MAX_RESEND_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail={
                "message":"Too many resend attempts. Please try again later.",
                "error_code":"OTP_TO_MANY_RESEND_ATTEMPTS"
            }
        )

    # 4️⃣ RESEND OTP
    otp = generate_otp()

    record.otp_hash = hash_otp(otp)
    record.expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    record.resend_count += 1

    await db.commit()

    send_otp_email(data.email, otp)

    return {
        "message": "OTP resent successfully",
        "expires_in_minutes": OTP_EXPIRY_MINUTES
    }


#######################################################
# ✅ VERIFY OTP (with expiry check)
#######################################################

# from sqlalchemy import delete

@router.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest, db: AsyncSession = Depends(get_session)):

    result = await db.execute(
        select(EmailOTP).where(EmailOTP.email == data.email)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=400, 
            detail={
                "message":"OTP not found",
                "error_code":"OTP not found"
            }
        )

    if record.expires_at < datetime.utcnow():
        await db.execute(
            delete(EmailOTP).where(EmailOTP.email == data.email)
        )
        await db.commit()
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "OTP expired",   
                "error_code": "OTP_EXPIRED"
            }
        )

    if record.otp_hash != hash_otp(data.otp):
        raise HTTPException(status_code=400,
         detail={
            "message":"Invalid OTP",
            "error_code": "OTP_INVALID"
         }
    )

    # success → delete OTP
    await db.execute(
        delete(EmailOTP).where(EmailOTP.email == data.email)
    )
    await db.commit()

    return {"message": "Email verified successfully"}
