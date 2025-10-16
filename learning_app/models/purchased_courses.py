from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime

class PurchasedCourse(Base):
    __tablename__ = "purchased_courses"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User")
    course = relationship("Course")
