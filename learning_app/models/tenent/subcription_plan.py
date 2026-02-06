from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from models.base import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    price = Column(Integer, nullable=False)
    billing_cycle = Column(String, nullable=False)  # monthly / yearly
    max_users = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
