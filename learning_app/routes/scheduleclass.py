from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import CourseCalendar, Course, Lesson, Batch
from database.db import get_session
from datetime import date
from pydantic import BaseModel

router = APIRouter(tags=["calendar"])

# ✅ Request body schema
class CourseCalendarCreate(BaseModel):
    batch_id: int
    lesson_id: int
    select_date : date
    day: str
    start_date: date
    end_date: date


@router.post("/add")
async def add_course_calendar(
    calendar_data: CourseCalendarCreate,
    db: AsyncSession = Depends(get_session),
):
    # Get the batch and related course
    result = await db.execute(select(Batch).where(Batch.id == calendar_data.batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Ensure batch belongs to a course
    if not batch.course_id:
        raise HTTPException(status_code=400, detail="Batch is not linked to a course")

    # Ensure lesson belongs to same course
    result = await db.execute(select(Lesson).where(Lesson.id == calendar_data.lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if lesson.course_id != batch.course_id:
        raise HTTPException(status_code=400, detail="Lesson does not belong to the batch's course")

    new_calendar_entry = CourseCalendar(
        course_id=batch.course_id,  # ✅ use course_id from batch
        batch_id=calendar_data.batch_id,
        lesson_id=calendar_data.lesson_id,
        day=calendar_data.day,
        select_date=calendar_data.select_date,
        start_date=calendar_data.start_date,
        end_date=calendar_data.end_date,
    )

    db.add(new_calendar_entry)
    await db.commit()
    await db.refresh(new_calendar_entry)

    return {
        "status": "success",
        "message": "Course calendar entry added successfully",
        "data": {
            "calendar_id": new_calendar_entry.id,
            "batch_id": new_calendar_entry.batch_id,
            "lesson_id": new_calendar_entry.lesson_id,
            "day": new_calendar_entry.day,
            "select_date": str(new_calendar_entry.select_date),
            "start_date": str(new_calendar_entry.start_date),
            "end_date": str(new_calendar_entry.end_date),
        },
    }
