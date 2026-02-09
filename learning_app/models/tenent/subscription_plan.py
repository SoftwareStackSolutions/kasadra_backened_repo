from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func

from models.base import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String(50), unique=True, nullable=False)
    price_usd = Column(Numeric(10, 2), nullable=False)

    max_users = Column(Integer)
    max_projects = Column(Integer)

    reporting = Column(String(50))
    support = Column(String(50))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
