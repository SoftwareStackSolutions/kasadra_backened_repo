from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import ScheduleClass
from models.course import Course, Lesson, CourseCalendar, Batch
from models.user import User
from database.db import get_session
from schemas.course import ScheduleCreate, ScheduleResponse
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from pydantic import BaseModel


router = APIRouter()

class CourseCalendarCreate(BaseModel):
    course_id: int
    batch_id: int
    lesson_id: int          # ✅ use lesson_id instead of lesson_title for consistency
    lesson_no: int
    day: str
    start_date: date
    end_date: date
    
# ✅ Add Schedule
@router.post("/add", response_model=ScheduleResponse, tags=["schedule"])
async def add_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_session)
):
    # Check course
    result = await db.execute(select(Course).where(Course.id == schedule.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check lesson
    result = await db.execute(select(Lesson).where(Lesson.id == schedule.lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    new_schedule = ScheduleClass(
        course_id=schedule.course_id,
        lesson_id=schedule.lesson_id,
        instructor_id=schedule.instructor_id,
        session_date=schedule.session_date,
        session_time=schedule.session_time
    )

    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)

    return new_schedule


# ✅ Get all schedules for a course
@router.get("/schedule/{course_id}", tags=["schedule"])
async def get_schedules(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(ScheduleClass)
        .options(selectinload(ScheduleClass.lesson))  # preload lesson
        .where(ScheduleClass.course_id == course_id)
    )
    schedules = result.scalars().all()

    if not schedules:
        return {"schedules": [], "message": "No schedules found"}

    return {
        "schedules": [
            {
                "id": s.id,
                "course_id": s.course_id,
                "lesson_id": s.lesson_id,
                "lesson_title": s.lesson.lesson_title if s.lesson else None,
                "instructor_id": s.instructor_id,
                "session_date": s.session_date.strftime("%Y-%m-%d"),
                "session_time": str(s.session_time),
            }
            for s in schedules
        ]
    }

# ✅ Add Course Calendar Entry
@router.post("/add", tags=["calendar"])
async def add_course_calendar(
    calendar_data: CourseCalendarCreate,
    db: AsyncSession = Depends(get_session),
):
    # ✅ 1. Validate Course
    course = await db.get(Course, calendar_data.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {calendar_data.course_id} not found",
        )

    # ✅ 2. Validate Batch
    batch = await db.get(Batch, calendar_data.batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {calendar_data.batch_id} not found",
        )
    if batch.course_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This batch does not belong to the specified course.",
        )

    # ✅ 3. Validate Lesson
    lesson = await db.get(Lesson, calendar_data.lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {calendar_data.lesson_id} not found",
        )
    if lesson.course_id != course.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This lesson does not belong to the specified course.",
        )

    # ✅ 4. Create Calendar Entry
    new_calendar_entry = CourseCalendar(
        course_id=calendar_data.course_id,
        batch_id=calendar_data.batch_id,
        lesson_id=calendar_data.lesson_id,
        lesson_no=calendar_data.lesson_no,
        lesson_title=lesson.lesson_title,  # auto fetch from DB ✅
        day=calendar_data.day,
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
            "course_id": new_calendar_entry.course_id,
            "batch_id": new_calendar_entry.batch_id,
            "lesson_id": new_calendar_entry.lesson_id,
            "lesson_no": new_calendar_entry.lesson_no,
            "lesson_title": new_calendar_entry.lesson_title,
            "day": new_calendar_entry.day,
            "start_date": str(new_calendar_entry.start_date),
            "end_date": str(new_calendar_entry.end_date),
        },
    }