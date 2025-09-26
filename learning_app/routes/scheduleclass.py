from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import ScheduleClass
from models.course import Course, Lesson
from models.user import User
from database.db import get_session
from schemas.course import ScheduleCreate, ScheduleResponse

router = APIRouter()

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
    result = await db.execute(select(ScheduleClass).where(ScheduleClass.course_id == course_id))
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
