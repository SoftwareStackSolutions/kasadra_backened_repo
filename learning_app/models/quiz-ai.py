from sqlalchemy import Column, Integer, String, Date,ForeignKey, LargeBinary, Text, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date
from models.user import User
from sqlalchemy import Time,  UniqueConstraint
from models.course import Course
from models.course import Lesson
from .base import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)

    # Relations
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Quiz info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # AI / Manual
    source = Column(
        Enum("manual", "ai", name="quiz_source_enum"),
        nullable=False,
        default="manual"
    )

    # Versioning & control
    version = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)

    # Optional (if quiz exported as PDF later)
    file_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="quizzes")
    lesson = relationship("Lesson", back_populates="quizzes")
    creator = relationship("User")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))

    question = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)

    correct_option = Column(String, nullable=False)

    quiz = relationship("Quiz", backref="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    attempted_at = Column(DateTime, server_default=func.now())


attempt_count = await db.execute(
    select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id)
)

if attempt_count.scalars().first():
    quiz.is_locked = True

