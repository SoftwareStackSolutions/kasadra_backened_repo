import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, LargeBinary

from models.base import Base

class Student(Base):
    __tablename__ = "student"

    student_id=Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    student_name=Column(String,unique=True, nullable=False)
    full_name=Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


class TokenTable(Base):
    __tablename__ = "token1"

    student_id = Column(Integer, ForeignKey(Student.student_id), nullable=False)
    access_token = Column(String(450), primary_key=True)
    refresh_token = Column(String(450), nullable=False)
    status = Column(Boolean)
    created_date = Column(DateTime, default=datetime.datetime.now)  