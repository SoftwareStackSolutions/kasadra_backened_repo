from sqlalchemy import Column, Integer, String, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from datetime import date
from sqlalchemy import Time
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



class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # instructor_name = Column(String, ForeignKey("users.name"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    file_url = Column(String, nullable=True)  # s
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
    file_url = Column(String, nullable=True)  # s
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
    description = Column(String, nullable=True)
    quiz_link = Column(String, nullable=True) 
    file_url = Column(String(500), nullable=True)  # new field
    created_at = Column(Date, default=date.today)

    concept = relationship("Concept", back_populates="quizzes")
    

class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String, nullable=True)  
    lab_link = Column(String, nullable=True)
    created_at = Column(Date, default=date.today)
    
    concept = relationship("Concept", back_populates="labs")
    lesson = relationship("Lesson")   
    course = relationship("Course")


class ScheduleClass(Base):
    __tablename__ = "schedule_classes"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)

    session_date = Column(Date, nullable=False)
    session_time = Column(Time, nullable=False)
    created_at = Column(Date, default=date.today)

    instructor = relationship("User")
    course = relationship("Course")
    lesson = relationship("Lesson")


class Batch(Base):
    __tablename__ = "assign_batches"

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

class CourseCalendar(Base):
    __tablename__ = "course_calendar"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_no = Column(Integer, nullable=False)
    lesson_title = Column(String(255), nullable=False)
    day = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)

    # Relationship (optional)
    course = relationship("Course", back_populates="calendar_entries")
