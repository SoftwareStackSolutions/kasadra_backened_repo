from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timedelta
from models.base import Base

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    subscription_plan_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
