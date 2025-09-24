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
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(Text, nullable=False)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="options")




# class Token(Base):
#     __tablename__ = "tokens"
#     __table_args__ = {'extend_existing': True}

#     user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
#     access_token = Column(String(450), unique=True)
#     refresh_token = Column(String(450), nullable=False)
#     status = Column(Boolean)
#     created_at = Column(Date, default=date.today)
#     user = relationship(User, back_populates="token")