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

class CourseCalendarUpdate(BaseModel):
    batch_id: int | None = None
    lesson_id: int | None = None
    select_date: date | None = None
    day: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    
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
        return {"status": "success", "message": "No calendar entries found", "data": []}

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
            "start_date": str(c.start_date),
            "end_date": str(c.end_date),
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
        raise HTTPException(status_code=404, detail="Calendar entry not found")

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
        "message": f"Calendar entry {calendar_id} updated successfully",
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
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    await db.delete(calendar)
    await db.commit()

    return {
        "status": "success",
        "message": f"Calendar entry {calendar_id} deleted successfully"
    }