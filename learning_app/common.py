import pytz

from enum import Enum
from datetime import datetime, timezone, timedelta

from sqlalchemy.future import select
from sqlalchemy import func

from models.user import User

async def get_user_by_email(email: str, session):
    query_stmt = select(User).where(func.lower(User.email) == email.lower())
    result = await session.execute(query_stmt)
    return result.scalar()

