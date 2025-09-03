import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    instructor = "instructor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=False, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_no = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    confirm_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    token = relationship("Token", back_populates="user", uselist=False)

class Token(Base):
    __tablename__ = "tokens"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    access_token = Column(String(450), unique=True)
    refresh_token = Column(String(450), nullable=False)
    status = Column(Boolean)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="token")
