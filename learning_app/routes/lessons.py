from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, RoleEnum
from models.course import Course
from database.db import get_session
from datetime import datetime
from models.user import User
from sqlalchemy.future import select
from models.course import Course, Lesson
from schemas.course import CourseCreate, LessonCreate
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Form


from dependencies.auth_dep import get_current_user

router = APIRouter()
class LessonCreate(BaseModel):
    course_id: int
    title: str
    description: str = None
    file: UploadFile = None  # Assuming file is optional                                                                                                                                                                                                                                                                                


@router.post("/add", tags=["lessons"])
async def add_lesson(
    course_id: int,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_session)
):
    # check if course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    file_content = None
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        file_content = await file.read()

    new_lesson = Lesson(
        title=title,
        description=description,
        file_content=file_content,
        course_id=course.id
    )

    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)

    return {
        "status": "success",
        "message": "Lesson added successfully",
        "data": {"lesson_id": new_lesson.id, "title": new_lesson.title}
    }

@router.get("/all", tags=["lessons"])
async def get_all_lessons(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Lesson))
    lessons = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "course_id": lesson.course_id,
            }
            for lesson in lessons
        ]
    }