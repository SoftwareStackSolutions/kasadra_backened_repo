from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from datetime import date
from models.user import User


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    thumbnail = Column(String, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Date, default=date.today)
    #instructor = relationship(User, back_populates="courses")



# class Token(Base):
#     __tablename__ = "tokens"
#     __table_args__ = {'extend_existing': True}

#     user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
#     access_token = Column(String(450), unique=True)
#     refresh_token = Column(String(450), nullable=False)
#     status = Column(Boolean)
#     created_at = Column(Date, default=date.today)
#     user = relationship(User, back_populates="token")


