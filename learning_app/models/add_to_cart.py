from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class Cart(Base):
    __tablename__ = "add_to_cart"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    added_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="cart_items")
    course = relationship("Course", back_populates="cart_entries")
