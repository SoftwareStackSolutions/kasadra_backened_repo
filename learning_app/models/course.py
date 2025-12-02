from sqlalchemy import Column, Integer, String, Date,ForeignKey, LargeBinary, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date
from models.user import User
from sqlalchemy import Time,  UniqueConstraint

from .base import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)    # store file as binary
    created_at = Column(Date, default=date.today)

    instructor = relationship("User", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    cart_entries = relationship("Cart", back_populates="course", cascade="all, delete-orphan")
    calendar_entries = relationship("CourseCalendar", back_populates="course", cascade="all, delete")

    pdfs = relationship("Pdf", back_populates="course", cascade="all, delete-orphan")
    weblinks = relationship("WebLink", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="course", cascade="all, delete-orphan")
    meetings = relationship("MeetingLink", back_populates="course", cascade="all, delete")
    notes = relationship("Note", back_populates="course", cascade="all, delete")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # instructor_name = Column(String, ForeignKey("users.name"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(Date, default=date.today)
    
    instructor = relationship("User", foreign_keys=[instructor_id])
    course = relationship("Course", back_populates="lessons")
    pdfs = relationship("Pdf", back_populates="lesson", cascade="all, delete-orphan")
    weblinks = relationship("WebLink", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="lesson", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="lesson", cascade="all, delete")

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)
    num_students = Column(Integer, nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timing = Column(String, nullable=True)  # Can be "10:00-12:00" or separate start/end
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False) 
    created_at = Column(Date, default=date.today)

    course = relationship("Course")
    instructor = relationship("User")
    calendar_entries = relationship("CourseCalendar", back_populates="batch", cascade="all, delete-orphan")
    meetings = relationship("MeetingLink", back_populates="batch", cascade="all, delete")

class BatchStudent(Base):
    __tablename__ = "batch_students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    batch_name = Column(String, nullable=True)

    # 🔥 A student can only have ONE batch per course, not globally
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="unique_student_course_assignment"),
    )

    batch = relationship("Batch")
    student = relationship("User")



class CourseCalendar(Base):
    __tablename__ = "course_calendar"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True)  # ✅ FIX
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True)
    select_date = Column(Date, nullable=True)
    day = Column(String, nullable=False)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    # Relationships
    course = relationship("Course", back_populates="calendar_entries")
    batch = relationship("Batch", back_populates="calendar_entries")
    lesson = relationship("Lesson")

class MeetingLink(Base):
    __tablename__ = "meeting_links"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))  # ✅ FIX
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"))
    meeting_url = Column(String(255), nullable=False)

    # Relationships (optional, for easy access)
    instructor = relationship("User", back_populates="meetings")
    course = relationship("Course", back_populates="meetings")
    batch = relationship("Batch", back_populates="meetings")


class Pdf(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    file_url = Column(String, nullable=False)
    created_at = Column(Date, default=date.today)

    course = relationship("Course", back_populates="pdfs")
    lesson = relationship("Lesson", back_populates="pdfs")


class WebLink(Base):
    __tablename__ = "weblinks"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    link_url = Column(String, nullable=False)
    created_at = Column(Date, default=date.today)

    course = relationship("Course", back_populates="weblinks")
    lesson = relationship("Lesson", back_populates="weblinks")
  

class Quiz(Base):
    __tablename__ = "quiz"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    
    course = relationship("Course", back_populates="quizzes")
    lesson = relationship("Lesson", back_populates="quizzes")

class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    
    course = relationship("Course", back_populates="labs")
    lesson = relationship("Lesson", back_populates="labs")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


    notes = Column(Text, nullable=False)
    course = relationship("Course", back_populates="notes", lazy="joined")
    lesson = relationship("Lesson", back_populates="notes", lazy="joined")
    instructor = relationship("User")

###########################################
## BatchLessonActivation
###########################################

class BatchLessonActivation(Base):
    __tablename__ = "batch_lesson_activation"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional relationships
    batch = relationship("Batch", backref="activated_lessons")
    lesson = relationship("Lesson", backref="lesson_activations")

    __table_args__ = (
    UniqueConstraint('batch_id', 'lesson_id', name='unique_batch_lesson'),
)