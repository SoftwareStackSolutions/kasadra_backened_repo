import requests
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.holidays import Holiday

CALENDARIFIC_API_KEY = "RZjGdf6c3QGY7975Bh74moeKRjGODrKY"
CALENDARIFIC_URL = "https://calendarific.com/api/v2/holidays"


def fetch_holidays_from_calendarific(year: int, country: str = "IN"):
    params = {
        "api_key": CALENDARIFIC_API_KEY,
        "country": country,
        "year": year
    }
    response = requests.get(CALENDARIFIC_URL, params=params)
    response.raise_for_status()
    return response.json()["response"]["holidays"]


async def save_holidays_to_db(
    db: AsyncSession,
    holidays_data: list,
    year: int,
    country: str = "IN"
):
    for h in holidays_data:
        # ✅ ALWAYS extract only YYYY-MM-DD
        iso_date = h["date"]["iso"]
        holiday_date = datetime.strptime(
            iso_date.split("T")[0],
            "%Y-%m-%d"
        ).date()

        result = await db.execute(
            select(Holiday).where(
                Holiday.date == holiday_date,
                Holiday.country == country
            )
        )
        exists = result.scalar_one_or_none()

        if not exists:
            db.add(
                Holiday(
                    date=holiday_date,
                    name=h["name"],
                    country=country,
                    year=year
                )
            )

    await db.commit()


async def load_holidays_if_not_exists(
    db: AsyncSession,
    year: int,
    country: str = "IN"
):
    result = await db.execute(
        select(func.count()).select_from(Holiday).where(
            Holiday.year == year,
            Holiday.country == country
        )
    )
    count = result.scalar()

    if count == 0:
        holidays = fetch_holidays_from_calendarific(year, country)
        await save_holidays_to_db(db, holidays, year, country)




