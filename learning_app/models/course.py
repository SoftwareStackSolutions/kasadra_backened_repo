# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from .base import Base
# from .user import User

# class Course(Base):
#     __tablename__ = "courses"

#     id = Column(Integer, primary_key=True)
#     title = Column(String, nullable=False)
#     description = Column(String, nullable=False)
#     duration = Column(String, nullable=False)
#     instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     thumbnail = Column(String, nullable=True)  # store thumbnail URL/path

#     instructor = relationship("User", back_populates="courses")


# class User(Base):
#     __tablename__ = "users"
    
#     # existing fields...
#     token = relationship("Token", back_populates="user", uselist=False)
#     courses = relationship("Course", back_populates="instructor")  # add this
