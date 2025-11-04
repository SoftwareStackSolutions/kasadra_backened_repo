from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import ScheduleClass
from models.course import Course, Lesson, CourseCalendar
from models.user import User
from database.db import get_session
from schemas.course import ScheduleCreate, ScheduleResponse
from sqlalchemy.orm import selectinload
from datetime import datetime

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
                "lesson_title": s.lesson.title if s.lesson else None,
                "instructor_id": s.instructor_id,
                "session_date": s.session_date.strftime("%Y-%m-%d"),
                "session_time": str(s.session_time),
            }
            for s in schedules
        ]
    }

@router.post("/{course_id}/add", tags=["calendar"])
async def add_calendar_entry(
    course_id: int,
    lesson_no: int,
    lesson_title: str,
    day: str,
    date: str,  # Expecting something like '04-11-2025'
    time: str,  # Expecting something like '4pm' or '16:00'
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Validate course exists
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2️⃣ Parse date string to Python date
    try:
        parsed_date = datetime.strptime(date.strip(), "%d-%m-%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Please use DD-MM-YYYY (e.g., 04-11-2025)"
        )

    # 3️⃣ Parse time string to Python time
    try:
        # Handle both 12-hour and 24-hour formats
        if "am" in time.lower() or "pm" in time.lower():
            parsed_time = datetime.strptime(time.strip().lower(), "%I%p").time()
        else:
            parsed_time = datetime.strptime(time.strip(), "%H:%M").time()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid time format. Please use '4pm' or '16:00'"
        )

    # 4️⃣ Create calendar entry
    new_entry = CourseCalendar(
        course_id=course_id,
        lesson_no=lesson_no,
        lesson_title=lesson_title,
        day=day,
        date=parsed_date,  # ✅ correct Python date object
        time=parsed_time   # ✅ correct Python time object
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    return {
        "status": "success",
        "message": "Lesson added to calendar",
        "data": {
            "id": new_entry.id,
            "lesson_no": new_entry.lesson_no,
            "lesson_title": new_entry.lesson_title,
            "day": new_entry.day,
            "date": str(new_entry.date),
            "time": str(new_entry.time)
        }
    }


@router.get("/{course_id}/view",  tags=["calendar"])
async def view_course_calendar(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(CourseCalendar)
        .where(CourseCalendar.course_id == course_id)
        .order_by(CourseCalendar.lesson_no)
    )
    lessons = result.scalars().all()

    if not lessons:
        return {"status": "success", "data": [], "message": "No calendar entries for this course"}

    data = [
        {
            "lesson_no": l.lesson_no,
            "lesson_title": l.lesson_title,
            "day": l.day,
            "date": str(l.date),
            "time": str(l.time)
        } for l in lessons
    ]

    return {"status": "success", "data": data}
