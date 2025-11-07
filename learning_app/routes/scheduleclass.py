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
    course_id: int
    batch_id: int
    lesson_id: int
    select_date : date
    day: str
    start_date: date
    end_date: date


# ✅ Add Course Calendar Entry
@router.post("/add")
async def add_course_calendar(
    calendar_data: CourseCalendarCreate,
    db: AsyncSession = Depends(get_session),
):
    # 1️⃣ Check if course exists
    result = await db.execute(select(Course).where(Course.id == calendar_data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {calendar_data.course_id} not found"
        )

    # 2️⃣ Check if batch exists and belongs to course
    result = await db.execute(select(Batch).where(Batch.id == calendar_data.batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {calendar_data.batch_id} not found"
        )
    if batch.course_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This batch does not belong to the specified course."
        )

    # 3️⃣ Check if lesson exists and belongs to course
    result = await db.execute(select(Lesson).where(Lesson.id == calendar_data.lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {calendar_data.lesson_id} not found"
        )
    if lesson.course_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This lesson does not belong to the specified course."
        )

    # 4️⃣ Create new course calendar entry
    new_calendar_entry = CourseCalendar(
        course_id=calendar_data.course_id,
        batch_id=calendar_data.batch_id,
        lesson_id=calendar_data.lesson_id,
        lesson_title=lesson.lesson_title,  
        select_date=calendar_data.select_date,
        day=calendar_data.day,
        start_date=calendar_data.start_date,
        end_date=calendar_data.end_date,
    )

    db.add(new_calendar_entry)
    await db.commit()
    await db.refresh(new_calendar_entry)

    # ✅ Response same structure as schedule API
    return {
        "status": "success",
        "message": "Course calendar entry added successfully",
        "data": {
            "calendar_id": new_calendar_entry.id,
            "course_id": new_calendar_entry.course_id,
            "batch_id": new_calendar_entry.batch_id,
            "lesson_id": new_calendar_entry.lesson_id,
            "lesson_title": new_calendar_entry.lesson_title,
            "select_date": new_calendar_entry.select_date,
            "day": new_calendar_entry.day,
            "start_date": str(new_calendar_entry.start_date),
            "end_date": str(new_calendar_entry.end_date),
        },
    }
