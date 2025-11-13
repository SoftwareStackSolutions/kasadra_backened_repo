from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import CourseCalendar, Course, Lesson, Batch
from database.db import get_session
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["calendar"])

# ✅ Request body schema
class CourseCalendarCreate(BaseModel):
    course_id: int
    lesson_id: int
    day: str
    start_time: str  # store as string only (not actual time)
    end_time: str    # store as string only (not actual time)
    select_date: Optional[str] = None  # not used for storage, just received

class CourseCalendarUpdate(BaseModel):
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    select_date: Optional[str] = None  # ignored for DB


# ✅ API endpoint
@router.post("/add")
async def add_course_calendar(
    calendar_data: CourseCalendarCreate,
    db: AsyncSession = Depends(get_session),
):
    # ✅ Validate course
    result = await db.execute(select(Course).where(Course.id == calendar_data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # ✅ Validate lesson
    result = await db.execute(select(Lesson).where(Lesson.id == calendar_data.lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ✅ Ensure lesson belongs to the same course
    if lesson.course_id != calendar_data.course_id:
        raise HTTPException(status_code=400, detail="Lesson does not belong to the provided course")

    # ✅ Convert MM-DD-YYYY → date
    select_date_value = None
    if calendar_data.select_date:
        try:
            select_date_value = datetime.strptime(calendar_data.select_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Please use YYYY-MM-DD (e.g. 2025-11-13)."
            )

    # ✅ Create new record
    new_calendar_entry = CourseCalendar(
        course_id=calendar_data.course_id,
        lesson_id=calendar_data.lesson_id,
        day=calendar_data.day,
        start_time=calendar_data.start_time,
        end_time=calendar_data.end_time,
        select_date=select_date_value,
    )

    db.add(new_calendar_entry)
    await db.commit()
    await db.refresh(new_calendar_entry)

    return {
        "status": "success",
        "message": "schedule created successfully",
        "data": {
            "calendar_id": new_calendar_entry.id,
            "course_id": new_calendar_entry.course_id,
            "lesson_id": new_calendar_entry.lesson_id,
            "lesson_title": lesson.lesson_title,
            "day": new_calendar_entry.day,
            "start_time": new_calendar_entry.start_time,
            "end_time": new_calendar_entry.end_time,
            "select_date": new_calendar_entry.select_date.strftime("%Y-%m-%d") if new_calendar_entry.select_date else None,
        },
    }


# view calaneder by course ID
@router.get("/view/{course_id}")
async def get_course_calendar(course_id: int, db: AsyncSession = Depends(get_session)):
    # Check course existence
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(404, f"Course ID {course_id} not found")

    # Fetch calendar entries
    calendars = (await db.execute(
        select(CourseCalendar).where(CourseCalendar.course_id == course_id)
    )).scalars().all()

    if not calendars:
        return {"status": "success", "message": "No schedule class entries found", "data": []}

    # Build result
    data = []
    for c in calendars:
        batch = await db.get(Batch, c.batch_id)
        lesson = await db.get(Lesson, c.lesson_id)
        data.append({
            "calendar_id": c.id,
            "course_id": c.course_id,
            "batch_name": batch.batch_name if batch else None,
            "lesson_title": lesson.lesson_title if lesson else None,
            "select_date": str(c.select_date),
            "day": c.day,
            "start_time": str(c.start_time),
            "end_time": str(c.end_time),
        })

    return {"status": "success", "data": data}

# ✅ Update existing course calendar
@router.put("/update/{calendar_id}")
async def update_course_calendar(
    calendar_id: int,
    update_data: CourseCalendarUpdate,
    db: AsyncSession = Depends(get_session),
):
    calendar = await db.get(CourseCalendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Schedule class entry not found")

    # Update fields if provided
    if update_data.batch_id:
        batch = (await db.execute(select(Batch).where(Batch.id == update_data.batch_id))).scalar_one_or_none()
        if not batch:
            raise HTTPException(404, "Batch not found")
        calendar.batch_id = update_data.batch_id
        calendar.course_id = batch.course_id

    if update_data.lesson_id:
        lesson = (await db.execute(select(Lesson).where(Lesson.id == update_data.lesson_id))).scalar_one_or_none()
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        calendar.lesson_id = update_data.lesson_id

    if update_data.day:
        calendar.day = update_data.day
    if update_data.select_date:
        calendar.select_date = update_data.select_date
    if update_data.start_date:
        calendar.start_date = update_data.start_date
    if update_data.end_date:
        calendar.end_date = update_data.end_date

    await db.commit()
    await db.refresh(calendar)

    return {
        "status": "success",
        "message": f"Schedule class  updated successfully",
        "data": {
            "calendar_id": calendar.id,
            "batch_id": calendar.batch_id,
            "lesson_id": calendar.lesson_id,
            "day": calendar.day,
            "select_date": str(calendar.select_date),
            "start_date": str(calendar.start_date),
            "end_date": str(calendar.end_date),
        },
    }


# ✅ Delete course calendar
@router.delete("/delete/{calendar_id}")
async def delete_course_calendar(calendar_id: int, db: AsyncSession = Depends(get_session)):
    calendar = await db.get(CourseCalendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Schedule class entry not found")

    await db.delete(calendar)
    await db.commit()

    return {
        "status": "success",
        "message": f"Schedule class deleted successfully"
    }