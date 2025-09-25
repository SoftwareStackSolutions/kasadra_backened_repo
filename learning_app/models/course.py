from sqlalchemy import Text, Column, Integer, String, Date, DATETIME, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from .base import Base
from datetime import date
from models.user import User


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    thumbnail = Column(String, nullable=True)
    created_at = Column(Date, default=date.today)
    instructor = relationship("User", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # instructor_name = Column(String, ForeignKey("users.name"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    file_content = Column(LargeBinary, nullable=True)
    created_at = Column(Date, default=date.today)
    
    instructor = relationship("User", foreign_keys=[instructor_id])
    course = relationship("Course", back_populates="lessons")
    concepts = relationship("Concept", back_populates="lesson", cascade="all, delete-orphan")

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_content = Column(LargeBinary, nullable=True)
    created_at = Column(Date, default=date.today)

    lesson = relationship("Lesson", back_populates="concepts")
    quizzes = relationship("Quiz", back_populates="concept", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="concept", cascade="all, delete-orphan")

    


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    quiz_link = Column(String, nullable=True)   # new field
    created_at = Column(Date, default=date.today)

    concept = relationship("Concept", back_populates="quizzes")
    

class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_content = Column(LargeBinary, nullable=True)
    lab_link = Column(String, nullable=True)
    created_at = Column(Date, default=date.today)
    
    concept = relationship("Concept", back_populates="labs")
    lesson = relationship("Lesson")   
    course = relationship("Course")


