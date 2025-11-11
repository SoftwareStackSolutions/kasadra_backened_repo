import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import Base
from datetime import datetime, date


class RoleEnum(str, enum.Enum):
    student = "student"
    instructor = "instructor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=False, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_no = Column(String, unique=True, nullable=False)
    created_at = Column(Date, default=date.today)  
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    token = relationship("Token", back_populates="user", uselist=False)
    courses = relationship("Course", back_populates="instructor")
    cart_items = relationship("Cart", back_populates="student", cascade="all, delete-orphan")
    meetings = relationship("MeetingLink", back_populates="instructor", cascade="all, delete")



class Token(Base):
    __tablename__ = "tokens"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    access_token = Column(String(450), unique=True)
    refresh_token = Column(String(450), nullable=False)
    status = Column(Boolean)
    created_at = Column(Date, default=date.today)  
    user = relationship("User", back_populates="token")


