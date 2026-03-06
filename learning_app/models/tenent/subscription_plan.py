from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
import enum
import uuid
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

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)

    org_name = Column(String, nullable=False)

    # email = Column(String, nullable=False, unique=True, index=True) 
    email = Column(String, nullable=False, index=True)

    domain_name = Column(String, nullable=False, index=True)
    site_url = Column(String, nullable=False, index=True)

    subscription_id = Column(
        Integer,
        ForeignKey("subscription_plans.id"),
        nullable=False
    )

    password_hash = Column(String, nullable=False)
    invites = relationship("InvitedUser", back_populates="tenant")
    users = relationship("OrganizationUsers", back_populates="tenant")

