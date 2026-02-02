from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from models.base import Base

class EmailOTP(Base):
    __tablename__ = "email_otp"

    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
