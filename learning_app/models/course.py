from sqlalchemy import Column, Integer, String, Date, DATETIME, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from .base import Base
from datetime import date
from models.user import User
# from typing import Optional
# from pydantic import BaseModel


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
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    file_content = Column(LargeBinary, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(Date, default=date.today)

    course = relationship("Course", back_populates="lessons")
    contents = relationship("Content", back_populates="lesson")

class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    lesson_title = Column(String, nullable=False)
    concept_title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_content = Column(LargeBinary, nullable=True)
    created_at = Column(Date, default=date.today)

    lesson = relationship("Lesson", back_populates="contents")

# class LessonCreate(BaseModel):
    # description: Optional[str] = None




# class Token(Base):
#     __tablename__ = "tokens"
#     __table_args__ = {'extend_existing': True}

#     user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
#     access_token = Column(String(450), unique=True)
#     refresh_token = Column(String(450), nullable=False)
#     status = Column(Boolean)
#     created_at = Column(Date, default=date.today)
#     user = relationship(User, back_populates="token")