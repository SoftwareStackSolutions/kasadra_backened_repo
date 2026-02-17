from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy.sql import func
from models.base import Base

class EmailOTP(Base):
    __tablename__ = "email_otp"

    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, unique=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    resend_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)