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
    
    # Check if course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")


    # Handle file
    file_content = None
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        file_content = await file.read()

    # Create lesson
    new_lesson = Lesson(
        instructor_id = instructor_id,
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
        "data": {"lesson_id": new_lesson.id, "instructor_id": instructor_id, "course_id": course.id, "title": new_lesson.title},
    }

# Get all lessons
@router.get("/all", tags=["lessons"])
async def get_all_lessons(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Lesson).options(selectinload(Lesson.course))  # 👈 eagerly load course
    )
    lessons = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "id": lesson.id,
                "instructor_id": lesson.instructor_id,
                "course_name": lesson.course.title if lesson.course else None,
                "course_id": lesson.course_id,
                "title": lesson.title,
                "description": lesson.description,
                "created_at": lesson.created_at
            }
            for lesson in lessons
        ]
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

# @router.get("/course/{course_id}", tags=["lessons"])
# async def get_lessons_by_course(
#     course_id: int,
#     db: AsyncSession = Depends(get_session),
# ):
#     # Fetch lessons for the course
#     result = await db.execute(
#         select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.created_at.desc())
#     )
#     lessons = result.scalars().all()

#     if not lessons:
#         raise HTTPException(status_code=404, detail="No lessons found for this course")

#     return [
#         {
#             "id": lesson.id,
#             "instructor_id": lesson.instructor_id,
#             "title": lesson.title,
#             "description": lesson.description,
#             "created_at": lesson.created_at,
#         }
#         for lesson in lessons
#     ]

# @router.get("/course/{course_id}", tags=["lessons"])
# async def get_lessons_by_course(
#     course_id: int,
#     db: AsyncSession = Depends(get_session),
# ):
#     result = await db.execute(
#         select(Lesson)
#         .options(selectinload(Lesson.concepts))
#         .options(selectinload(Lesson.course))
#         .where(Lesson.course_id == course_id)
#         .order_by(Lesson.created_at.desc())
#     )
#     lessons = result.scalars().all()

#     if not lessons:
#         raise HTTPException(status_code=404, detail="No lessons found for this course")

#     response = []
#     for lesson in lessons:
#         response.append({
#             "id": lesson.id,
#             "lesson": lesson.title,
#             "courseName": lesson.course.title if lesson.course else None,
#             "sessionDate": lesson.created_at.strftime("%Y-%m-%d"),
#             # releaseTime won't work with Date, so just return None or add DateTime in model
#             "releaseTime": None,  
#             "status": "Active",  # or add a status field in Lesson model
#             "concepts": [
#                 {
#                     "id": concept.id,
#                     "title": concept.title,
#                     "quiz": getattr(concept, "quiz", False),  # default False
#                     "lab": getattr(concept, "lab", False),    # default False
#                 }
#                 for concept in lesson.concepts
#             ],
#         })

#     return response


@router.get("/course/{course_id}", tags=["lessons"])
async def get_lessons_by_course(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.concepts), selectinload(Lesson.course))
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.created_at.desc())
    )
    lessons = result.scalars().all()

    if not lessons:
        # ✅ Return empty response with custom message
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
                    "quiz": getattr(concept, "quiz", False),
                    "lab": getattr(concept, "lab", False),
                }
                for concept in lesson.concepts
            ],
        }
        for lesson in lessons
    ]

    return {"lessons": lessons_response}