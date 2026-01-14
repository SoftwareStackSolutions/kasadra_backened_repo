from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database.db import get_session
from holidaydir.holidaydb import load_holidays_if_not_exists
from models.holidays import Holiday

router = APIRouter()


@router.get("/holiday", tags=["Holidays"] )
async def get_holidays(
    startDate: str = Query(),
    endDate: str = Query(),
    country: str = "IN",
    db: AsyncSession = Depends(get_session)
):
    #start_date = datetime.strptime(startDate, "%Y-%m-%d").date()
    start_date = datetime.strptime(startDate, "%d-%m-%Y").date()
    end_date = datetime.strptime(endDate, "%d-%m-%Y").date()

    # Ensure holidays exist for that year
    await load_holidays_if_not_exists(db, start_date.year, country)

    result = await db.execute(
        select(Holiday).where(
            Holiday.country == country,
            Holiday.date.between(start_date, end_date)
        )
    )

    holidays = result.scalars().all()

    return [
        {
            "date": h.date,
            "name": h.name
        }
        for h in holidays
    ]
