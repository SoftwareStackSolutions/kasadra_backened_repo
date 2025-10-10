from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, RoleEnum
from models.course import Lesson
from models.course import Course
from models.course import Concept
from routes import course
from database.db import get_session
from datetime import datetime
from models.user import User
from sqlalchemy.future import select
from models.course import Course, Lesson
from schemas.course import CourseCreate, LessonCreate
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Form
from typing import Optional
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse

from dependencies.auth_dep import get_current_user

router = APIRouter()
class LessonCreate(BaseModel):
    title: str
    description: str = None
    file: UploadFile = None
    course_id: Optional[int] = None  # Assuming course_id is optional

@router.post("/add", tags=["lessons"])
async def add_lesson(
    instructor_id: int = Form(...),
    course_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # 1) Verify instructor exists and is an instructor
    result = await db.execute(select(User).where(User.id == instructor_id))
    instructor = result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    if instructor.role != RoleEnum.instructor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an instructor")

    # 2) Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # 3) Ensure the course was created by the provided instructor
    if course.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course was not created by the provided instructor"
        )

    # 4) Handle uploaded file (PDF only)
    file_content = None
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files allowed")
        file_content = await file.read()

    # 5) Create lesson
    new_lesson = Lesson(
        instructor_id=instructor_id,
        course_id=course.id,
        title=title,
        description=description,
        file_content=file_content,
        created_at=datetime.utcnow(),
    )

    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)

    return {
        "status": "success",
        "message": "Lesson added successfully",
        "data": {
            "lesson_id": new_lesson.id,
            "instructor_id": instructor_id,
            "course_id": course.id,
            "title": new_lesson.title,
        },
    }


@router.get("/all", tags=["lessons"])
async def get_all_lessons(db: AsyncSession = Depends(get_session)):
    from models.course import ScheduleClass  # import inside to avoid circular dependency

    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.course))
    )
    lessons = result.scalars().all()

    data = []
    for lesson in lessons:
        # Fetch the schedule for each lesson (if any)
        schedule_result = await db.execute(
            select(ScheduleClass)
            .where(ScheduleClass.lesson_id == lesson.id)
        )
        schedule = schedule_result.scalar_one_or_none()

        data.append({
            "id": lesson.id,
            "instructor_id": lesson.instructor_id,
            "course_name": lesson.course.title if lesson.course else None,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "description": lesson.description,
            "created_at": lesson.created_at,
            "session_date": schedule.session_date.strftime("%Y-%m-%d %H:%M") if schedule and schedule.session_date else None,
            "release_time": schedule.release_time if schedule and hasattr(schedule, "release_time") else "Not set",
            "status": "Scheduled" if schedule else "Not Scheduled"
        })

    return {
        "status": "success",
        "data": data
    }

# Get lesson by ID
@router.get("/{lesson_id}", tags=["lessons"])
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_session),
):
    # Query lesson by ID
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {
        "id": lesson.id,
        "instructor_id": lesson.instructor_id,
        "course_id": lesson.course_id,
        "title": lesson.title,
        "description": lesson.description,
        "created_at": lesson.created_at,
    }




@router.get("{course_id}", tags=["lessons"])
async def get_lessons_by_course(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.concepts).selectinload(Concept.quizzes),
                 selectinload(Lesson.concepts).selectinload(Concept.labs),
                 selectinload(Lesson.course))
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.created_at.desc())
    )
    lessons = result.scalars().all()

    if not lessons:
        return {"lessons": [], "message": "No lessons added yet"}

    lessons_response = [
        {
            "id": lesson.id,
            "lesson": lesson.title,
            "courseName": lesson.course.title if lesson.course else None,
            "sessionDate": lesson.created_at.strftime("%Y-%m-%d"),
            "releaseTime": None,
            "status": "Active",
            "concepts": [
                {
                    "id": concept.id,
                    "title": concept.title,
                    "quiz": len(concept.quizzes) > 0,
                    "lab": len(concept.labs) > 0,
                }
                for concept in lesson.concepts
            ],
        }
        for lesson in lessons
    ]

    return {"lessons": lessons_response}

