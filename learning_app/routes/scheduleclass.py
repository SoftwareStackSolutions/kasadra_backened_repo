from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import CourseCalendar, Course, Batch
from database.db import get_session
from datetime import datetime, time, timedelta
from pydantic import BaseModel
from typing import Optional
from models.holidays import Holiday
from typing import Literal, List
from models.user import User,RoleEnum
from models.course import BatchStudent

router = APIRouter(tags=["calendar"])

class CourseCalendarCreate(BaseModel):
    course_id: int
    batch_id: Optional[int] = None

    start_date: str   # "2026-01-01"
    end_date: str     # "2026-01-30"

    schedule_type: Literal["weekdays", "weekends", "custom"]
    custom_dates: Optional[List[str]] = []

    start_time: time  # "10:00:00"
    end_time: time    # "12:00:00"


# Date Generator Helper (Weekdays / Weekends / Custom)
from datetime import datetime, timedelta

def generate_schedule_dates(start_date, end_date, schedule_type, custom_dates):
    dates = []

    if schedule_type == "custom":
        for d in custom_dates:
            dates.append(datetime.strptime(d, "%d-%m-%Y").date())
        return dates

    current = start_date
    while current <= end_date:
        weekday = current.weekday()  # 0=Mon, 6=Sun

        if schedule_type == "weekdays" and weekday < 5:
            dates.append(current)

        if schedule_type == "weekends" and weekday >= 5:
            dates.append(current)

        current += timedelta(days=1)

    return dates

# API Endpoint

@router.post("/add")
async def add_course_calendar(
    calendar_data: CourseCalendarCreate,
    db: AsyncSession = Depends(get_session),
):
    # ----------------------------
    # 1. Validate Course
    # ----------------------------
    course = await db.scalar(
        select(Course).where(Course.id == calendar_data.course_id)
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # ----------------------------
    # 2. Validate Batch (optional)
    # ----------------------------
    if calendar_data.batch_id:
        batch = await db.scalar(
            select(Batch).where(Batch.id == calendar_data.batch_id)
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

    # ----------------------------
    # 3. Convert Dates
    # ----------------------------
    start_date = datetime.strptime(calendar_data.start_date, "%d-%m-%Y").date()
    end_date = datetime.strptime(calendar_data.end_date, "%d-%m-%Y").date()

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    # ----------------------------
    # 4. Fetch Holidays
    # ----------------------------
    holiday_rows = await db.execute(select(Holiday.date))
    holiday_dates = {row[0] for row in holiday_rows.all()}

    # ----------------------------
    # 5. Fetch Existing Scheduled Dates
    # ----------------------------
    existing_rows = await db.execute(
        select(CourseCalendar.select_date).where(
            CourseCalendar.course_id == calendar_data.course_id,
            CourseCalendar.batch_id == calendar_data.batch_id
        )
    )
    existing_dates = {row[0] for row in existing_rows.all()}

    # ----------------------------
    # 6. Generate Dates
    # ----------------------------
    generated_dates: List[datetime.date] = []

    if calendar_data.schedule_type == "custom":
        for d in calendar_data.custom_dates:
            date_obj = datetime.strptime(d, "%d-%m-%Y").date()
            generated_dates.append(date_obj)

    else:
        current = start_date
        while current <= end_date:
            weekday = current.weekday()  # 0=Mon, 6=Sun

            if calendar_data.schedule_type == "weekdays" and weekday < 5:
                generated_dates.append(current)

            elif calendar_data.schedule_type == "weekends" and weekday >= 5:
                generated_dates.append(current)

            current += timedelta(days=1)

    # ----------------------------
    # 7. Create Calendar Entries
    # ----------------------------
    entries = []

    for date in generated_dates:
        if date in holiday_dates:
            continue  # ❌ skip holidays

        if date in existing_dates:
            continue  # ❌ skip duplicates

        entries.append(
            CourseCalendar(
                course_id=calendar_data.course_id,
                batch_id=calendar_data.batch_id,
                select_date=date,
                start_time=calendar_data.start_time,
                end_time=calendar_data.end_time,
            )
        )

    if not entries:
        return {
            "status": "success",
            "message": "No new schedule created (all dates skipped)",
            "created_count": 0
        }

    # ----------------------------
    # 8. Save to DB
    # ----------------------------
    db.add_all(entries)
    await db.commit()

    # ----------------------------
    # 9. Response
    # ----------------------------
    return {
    "status": "success",
    "message": "Schedule created successfully",
    "created_count": len(entries),
        "dates": [
            {
                "date": e.select_date.strftime("%d-%m-%Y"),
                "start_time": e.start_time.strftime("%I:%M:%S %p").lower() if e.start_time else None,
                "end_time": e.end_time.strftime("%I:%M:%S %p").lower() if e.end_time else None
            }
            for e in entries
        ]
    }

######################################################################

# view calaneder by course ID

@router.get("/view/{course_id}")
async def get_course_calendar(
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # ----------------------------
    # 1. Validate Course
    # ----------------------------
    course = await db.scalar(
        select(Course).where(Course.id == course_id)
    )
    if not course:
        raise HTTPException(
            status_code=404,
            detail=f"Course ID {course_id} not found"
        )

    # ----------------------------
    # 2. Fetch Calendar + Batch
    # ----------------------------
    result = await db.execute(
        select(
            CourseCalendar,
            Batch.batch_name
        )
        .outerjoin(Batch, Batch.id == CourseCalendar.batch_id)
        .where(CourseCalendar.course_id == course_id)
        .order_by(CourseCalendar.select_date)
    )

    rows = result.all()

    if not rows:
        return {
            "status": "success",
            "message": "No schedule class entries found",
            "data": []
        }

    # ----------------------------
    # 3. Build Response
    # ----------------------------
    data = []
    for calendar, batch_name in rows:
        data.append({
            "calendar_id": calendar.id,
            "course_id": calendar.course_id,
            "batch_name": batch_name,
            "date": calendar.select_date.strftime("%d-%m-%Y"),
            "day": calendar.select_date.strftime("%A"),
            "start_time": calendar.start_time.strftime("%I:%M:%S %p").lower() if calendar.start_time else None,
            "end_time": calendar.end_time.strftime("%I:%M:%S %p").lower() if calendar.end_time else None,
        })

    return {
        "status": "success",
        "count": len(data),
        "data": data
    }


#############################
## Updated Calander
#############################

class CourseCalendarUpdate(BaseModel):
    course_id: int
    batch_id: Optional[int] = None
    select_date: str   
    start_time: Optional[time] = None
    end_time: Optional[time] = None


@router.put("/update/{calendar_id}")
async def update_course_calendar(
    calendar_id: int,
    calendar_data: CourseCalendarUpdate,
    db: AsyncSession = Depends(get_session),
):
    # ----------------------------
    # 1. Fetch Calendar Entry
    # ----------------------------
    calendar = await db.get(CourseCalendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    # ----------------------------
    # 2. Validate Course
    # ----------------------------
    course = await db.scalar(
        select(Course).where(Course.id == calendar_data.course_id)
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # ----------------------------
    # 3. Validate Batch (optional)
    # ----------------------------
    if calendar_data.batch_id:
        batch = await db.scalar(
            select(Batch).where(Batch.id == calendar_data.batch_id)
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

    # ----------------------------
    # 4. Convert Date (ANY DATE ALLOWED)
    # ----------------------------
    select_date = datetime.strptime(
        calendar_data.select_date, "%d-%m-%Y"
    ).date()

    # ----------------------------
    # 5. Prevent duplicate date (same course + batch)
    # ----------------------------
    duplicate = await db.scalar(
        select(CourseCalendar).where(
            CourseCalendar.course_id == calendar_data.course_id,
            CourseCalendar.batch_id == calendar_data.batch_id,
            CourseCalendar.select_date == select_date,
            CourseCalendar.id != calendar_id
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Another class already exists on this date"
        )

    # ----------------------------
    # 6. Update ONLY provided fields
    # ----------------------------
    calendar.course_id = calendar_data.course_id
    calendar.batch_id = calendar_data.batch_id
    calendar.select_date = select_date

    # 👉 IMPORTANT PART
    if calendar_data.start_time is not None:
        calendar.start_time = calendar_data.start_time

    if calendar_data.end_time is not None:
        calendar.end_time = calendar_data.end_time

    await db.commit()
    await db.refresh(calendar)

    # ----------------------------
    # 7. Response
    # ----------------------------
    return {
        "status": "success",
        "message": "Schedule updated successfully",
        "data": {
            "calendar_id": calendar.id,
            "course_id": calendar.course_id,
            "batch_id": calendar.batch_id,
            "date": calendar.select_date.strftime("%d-%m-%Y"),
            "day": calendar.select_date.strftime("%A"),
            "start_time": calendar.start_time.strftime("%I:%M:%S %p").lower(),
            "end_time": calendar.end_time.strftime("%I:%M:%S %p").lower(),
        }
    }


@router.delete("/delete/{calendar_id}")
async def delete_course_calendar(
    calendar_id: int,
    db: AsyncSession = Depends(get_session)
):
    # ----------------------------
    # 1. Fetch Calendar Entry
    # ----------------------------
    calendar = await db.get(CourseCalendar, calendar_id)
    if not calendar:
        raise HTTPException(
            status_code=404,
            detail="Course schedule not found"
        )

    # ----------------------------
    # 2. Delete Entry
    # ----------------------------
    await db.delete(calendar)
    await db.commit()

    # ----------------------------
    # 3. Response
    # ----------------------------
    return {
        "status": "success",
        "message": "Schedule deleted successfully",
        # "data": {
        #     "calendar_id": calendar_id,
        #     "course_id": calendar.course_id,
        #     "batch_id": calendar.batch_id,
        #     "date": calendar.select_date.strftime("%d-%m-%Y"),
        #     "start_time": calendar.start_time.strftime("%I:%M:%S %p").lower()
        #     if calendar.start_time else None,
        #     "end_time": calendar.end_time.strftime("%I:%M:%S %p").lower()
        #     if calendar.end_time else None,
        # }
    }


###############################################

## Owner AK Get all the dates in student side

@router.get("/student/{student_id}/{course_id}")
async def get_student_calendar(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # ----------------------------
    # 1. Validate Student
    # ----------------------------
    student = await db.get(User, student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    if student.role != RoleEnum.student:
        raise HTTPException(403, "User is not a student")

    # ----------------------------
    # 2. Find Student Batch
    # ----------------------------
    result = await db.execute(
        select(BatchStudent).where(BatchStudent.student_id == student_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(404, "Student is not assigned to any batch")

    batch = await db.get(Batch, mapping.batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")

    # ----------------------------
    # 3. Validate Course
    # ----------------------------
    if batch.course_id != course_id:
        raise HTTPException(400, "Student is not enrolled in this course")

    # ----------------------------
    # 4. Fetch Calendar Entries
    # ----------------------------
    calendars = (await db.execute(
        select(CourseCalendar)
        .where(
            CourseCalendar.course_id == course_id,
            CourseCalendar.batch_id == batch.id
        )
        .order_by(CourseCalendar.select_date.asc())
    )).scalars().all()

    if not calendars:
        return {
            "status": "success",
            "message": "No scheduled classes",
            "created_count": 0,
            "dates": []
        }

    # ----------------------------
    # 5. Build SAME Response as POST
    # ----------------------------
    return {
        "status": "success",
        "student_id": student_id,
        "course_id": course_id,
        "batch_id": batch.id,
        "batch_name": batch.batch_name,
        "created_count": len(calendars),
        "dates": [
            {
                "date": c.select_date.strftime("%d-%m-%Y"),
                "start_time": c.start_time.strftime("%I:%M:%S %p").lower()
                if c.start_time else None,
                "end_time": c.end_time.strftime("%I:%M:%S %p").lower()
                if c.end_time else None,
            }
            for c in calendars
        ]
    }
