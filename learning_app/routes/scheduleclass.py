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

################################################################
## POST API
################################################################

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
            continue 

        if date in existing_dates:
            continue  

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

################################################################
## GET API
################################################################

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
            "batch_id": calendar.batch_id,
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


################################################################
## PUT API
################################################################

from pydantic import BaseModel
from typing import List, Optional

class CalendarUpdateItem(BaseModel):
    calendar_id: int
    date: Optional[str] = None            # "18-01-2026"
    start_time: Optional[str] = None      # "03:00:00 pm"
    end_time: Optional[str] = None        # "06:00:00 pm"

class BulkCalendarUpdate(BaseModel):
    updates: List[CalendarUpdateItem]


from datetime import datetime, time

def parse_time(value: str) -> time:
    """
    Converts '03:00:00 pm' -> time(15, 0)
    """
    return datetime.strptime(value.lower(), "%I:%M:%S %p").time()



@router.put("/update", tags=["calendar"])
async def bulk_update_course_calendar(
    payload: BulkCalendarUpdate,
    db: AsyncSession = Depends(get_session)
):
    updated = []

    for item in payload.updates:
        calendar = await db.get(CourseCalendar, item.calendar_id)

        if not calendar:
            continue  # silently skip invalid IDs

        # ----------------------------
        # Update date (if provided)
        # ----------------------------
        if item.date:
            calendar.select_date = datetime.strptime(
                item.date, "%d-%m-%Y"
            ).date()

        # ----------------------------
        # Update time (if provided)
        # ----------------------------
        if item.start_time:
            calendar.start_time = parse_time(item.start_time)

        if item.end_time:
            calendar.end_time = parse_time(item.end_time)

        updated.append(calendar)

    if not updated:
        raise HTTPException(
            status_code=400,
            detail="No valid calendar entries updated"
        )

    await db.commit()

    # ----------------------------
    # Response (UI friendly)
    # ----------------------------
    return {
        "status": "success",
        "updated_count": len(updated),
        "data": [
            {
                "calendar_id": c.id,
                "date": c.select_date.strftime("%d-%m-%Y"),
                "start_time": c.start_time.strftime("%I:%M:%S %p").lower()
                if c.start_time else None,
                "end_time": c.end_time.strftime("%I:%M:%S %p").lower()
                if c.end_time else None
            }
            for c in updated
        ]
    }




################################################################
## Delete API
################################################################

class CalendarDeleteRequest(BaseModel):
    calendar_ids: list[int]


@router.delete("/delete")
async def delete_course_calendar(
    payload: CalendarDeleteRequest,
    db: AsyncSession = Depends(get_session)
):
    if not payload.calendar_ids:
        raise HTTPException(
            status_code=400,
            detail="No schedule selected for deletion"
        )

    result = await db.execute(
        select(CourseCalendar).where(
            CourseCalendar.id.in_(payload.calendar_ids)
        )
    )

    calendars = result.scalars().all()

    if not calendars:
        raise HTTPException(
            status_code=404,
            detail="No matching schedules found"
        )

    for calendar in calendars:
        await db.delete(calendar)

    await db.commit()

    return {
        "status": "success",
        "message": f"{len(calendars)} schedule(s) deleted successfully"
    }



###############################################
## Owner AK Get all the dates in student side
###############################################


# @router.get("/student/{student_id}/{course_id}")
# async def get_student_calendar(
#     student_id: int,
#     course_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     # ----------------------------
#     # 1. Validate Student
#     # ----------------------------
#     student = await db.get(User, student_id)
#     if not student:
#         raise HTTPException(404, "Student not found")

#     if student.role != RoleEnum.student:
#         raise HTTPException(403, "User is not a student")

#     # ----------------------------
#     # 2. Find Student Batch
#     # ----------------------------
#     result = await db.execute(
#         select(BatchStudent).where(BatchStudent.student_id == student_id)
#     )
#     mapping = result.scalar_one_or_none()

#     if not mapping:
#         raise HTTPException(404, "Student is not assigned to any batch")

#     batch = await db.get(Batch, mapping.batch_id)
#     if not batch:
#         raise HTTPException(404, "Batch not found")

#     # ----------------------------
#     # 3. Validate Course
#     # ----------------------------
#     # if batch.course_id != course_id:
#     #     raise HTTPException(400, "Student is not enrolled in this course")

#     # ----------------------------
#     # 4. Fetch Calendar Entries
#     # ----------------------------
#     calendars = (await db.execute(
#         select(CourseCalendar)
#         .where(
#             CourseCalendar.course_id == course_id,
#             CourseCalendar.batch_id == batch.id
#         )
#         .order_by(CourseCalendar.select_date.asc())
#     )).scalars().all()

#     if not calendars:
#         return {
#             "status": "success",
#             "message": "No scheduled classes",
#             "created_count": 0,
#             "dates": []
#         }

#     # ----------------------------
#     # 5. Build SAME Response as POST
#     # ----------------------------
#     return {
#         "status": "success",
#         "student_id": student_id,
#         "course_id": course_id,
#         "batch_id": batch.id,
#         "batch_name": batch.batch_name,
#         "created_count": len(calendars),
#         "dates": [
#             {
#                 "date": c.select_date.strftime("%d-%m-%Y"),
#                 "start_time": c.start_time.strftime("%I:%M:%S %p").lower()
#                 if c.start_time else None,
#                 "end_time": c.end_time.strftime("%I:%M:%S %p").lower()
#                 if c.end_time else None,
#             }
#             for c in calendars
#         ]
#     }


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
        raise HTTPException(status_code=404, detail="Student not found")

    if student.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="User is not a student")

    # ----------------------------
    # 2. Find Batch for this Student + Course
    # ----------------------------
    batch_result = await db.execute(
        select(Batch)
        .join(BatchStudent, BatchStudent.batch_id == Batch.id)
        .where(
            BatchStudent.student_id == student_id,
            Batch.course_id == course_id
        )
    )
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Student is not assigned to this course"
        )

    # ----------------------------
    # 3. Fetch Calendar Entries
    # ----------------------------
    calendars = (
        await db.execute(
            select(CourseCalendar)
            .where(
                CourseCalendar.course_id == course_id,
                CourseCalendar.batch_id == batch.id
            )
            .order_by(CourseCalendar.select_date.asc())
        )
    ).scalars().all()

    if not calendars:
        return {
            "status": "success",
            "message": "No scheduled classes",
            "created_count": 0,
            "dates": []
        }

    # ----------------------------
    # 4. SAME Response as POST
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
