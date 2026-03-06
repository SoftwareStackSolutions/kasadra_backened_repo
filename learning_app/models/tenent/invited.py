from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
import enum
import uuid
from models.base import Base
from models.tenent.subscription_plan import Organization

# -------------------------------
# Invited users
# -------------------------------

class RoleEnum(str, enum.Enum):
    student = "student"
    instructor = "instructor"

class InvitedUser(Base):
    __tablename__ = "invited_users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), nullable=False) 

    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Organization", back_populates="invites")

# -------------------------------
# Users Table
# -------------------------------

class OrganizationUsers(Base):
    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)

    password = Column(String, nullable=False)

    role = Column(Enum(RoleEnum), nullable=False)

    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Organization", back_populates="users")