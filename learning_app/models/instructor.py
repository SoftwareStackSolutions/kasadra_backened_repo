# import datetime
# from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, LargeBinary   
# from models.base import Base

# class Instructor(Base):
#     __tablename__ = "instructor"

#     instructor_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
#     name = Column(String, unique=False, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     mobile_no = Column(String, unique=False, nullable=False)
#     password = Column(String, nullable=False)
#     confirm_password = Column(String, nullable=False)

# class TokenTable(Base):
#     __tablename__ ="token"   

#     instructor_id = Column(Integer, ForeignKey(Instructor.instructor_id), nullable=False)
#     access_token = Column(String(450), primary_key=True)
#     refresh_token = Column(String(450), nullable=False)
#     status = Column(Boolean)
#     created_Date = Column(DateTime, default=datetime.datetime.now)
