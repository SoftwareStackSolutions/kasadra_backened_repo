import pytz


from enum import Enum
from datetime import datetime, timezone, timedelta

from sqlalchemy.future import select
from sqlalchemy import func

from models.student import Student
# from data.image_url import IMAGE_URL

class Weekday(Enum):
    mon = 0
    tue = 1
    wed = 2
    thu = 3
    fri = 4
    sat = 5
    sun = 6

async def get_student_by_email(request,session):
  email = (request.Email).lower()
  query_stmt = select(Student).where(func.lower(Student.email) == email)
  result = await session.execute(query_stmt)
  user = result.scalar()
  return user