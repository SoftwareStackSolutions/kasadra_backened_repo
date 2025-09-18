from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, RoleEnum
from models.course import Course
from database.db import get_session
from datetime import datetime
from models.user import User
from sqlalchemy.future import select
from models.course import Course, Lesson, Content
from schemas.course import CourseCreate, LessonCreate
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Form


from dependencies.auth_dep import get_current_user

router = APIRouter()

class CourseCreate(BaseModel):
    title: str
    description: str
    duration: str
    thumbnail: str 


################################
## Course ADD method
#################################
router = APIRouter()

from typing import Optional

class CourseCreate(BaseModel):
    title: str
    description: str
    duration: str
    thumbnail: Optional[str] = None
    instructor_id: Optional[int] = None  # Now optional for testing

@router.post("/add", tags=["courses"])
async def add_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_session)
):
    instructor_id = course.instructor_id or 1  # Default to instructor_id=1

    new_course = Course(
        title=course.title,
        description=course.description,
        duration=course.duration,
        thumbnail=course.thumbnail,
        instructor_id=instructor_id,
        created_at=datetime.utcnow()
    )

    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)

    return {
        "status": "success",
        "message": "Course added successfully",
        "data": {
            "course_id": new_course.id,
            "title": new_course.title
        }
    }

@router.post("/lessons/add", tags=["lessons"])
async def add_lesson(
    lesson: LessonCreate,
    db: AsyncSession = Depends(get_session)
):
    file_bytes = None
    if lesson.file_content:
        import base64
        file_bytes = base64.b64decode(lesson.file_content)

    new_lesson = Lesson(
        title=lesson.title,
        description=lesson.description,
        file_content=file_bytes,
        course_id=lesson.course_id,
    )

    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)

    return {
        "status": "success",
        "message": "Lesson added successfully",
        "data": {"lesson_id": new_lesson.id, "title": new_lesson.title}
    }

################################################################################
###############################
# Course ADD method
################################
router = APIRouter()

from typing import Optional

class CourseCreate(BaseModel):
    title: str
    description: str
    duration: str
    thumbnail: Optional[str] = None
    instructor_id: Optional[int] = None  # Now optional for testing

@router.post("/add", tags=["courses"])
async def add_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_session)
):
    instructor_id = course.instructor_id or 1  # Default to instructor_id=1

    new_course = Course(
        title=course.title,
        description=course.description,
        duration=course.duration,
        thumbnail=course.thumbnail,
        instructor_id=instructor_id,
        created_at=datetime.utcnow()
    )

    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)

    return {
        "status": "success",
        "message": "Course added successfully",
        "data": {
            "course_id": new_course.id,
            "title": new_course.title
        }
    }

@router.post("/courses/{course_id}/lessons/add", tags=["lessons"])
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

@router.post("/lessons/{lesson_id}/contents/add", tags=["contents"])
async def add_content(
    lesson_id: int,
    lesson_title: str = Form(...),
    concept_title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_session)
):
    # check if lesson exists
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    file_content = None
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        file_content = await file.read()

    new_content = Content(
        lesson_id=lesson.id,
        lesson_title=lesson_title,
        concept_title=concept_title,
        description=description,
        file_content=file_content
    )

    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)

    return {
        "status": "success",
        "message": "Content added successfully",
        "data": {"content_id": new_content.id, "concept_title": new_content.concept_title}
    }

################################
## Course GET method with JWT
################################# 
# @router.get("/courses", tags=["courses"])
# async def get_all_courses(
#     current_user: User = Depends(get_current_user),  # ✅ Require JWT auth
#     db: AsyncSession = Depends(get_session)
# ):
#     # ✅ Only allow instructors to access this API
#     if current_user.role != RoleEnum.instructor:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access forbidden: only instructors can view the courses"
#         )

#     result = await db.execute(
#         select(
#             Course.id,
#             Course.title,
#             Course.description,
#             Course.duration,
#             Course.thumbnail,
#             Course.created_at,
#             Course.instructor_id,
#             User.name.label("instructor_name")
#         ).join(User, User.id == Course.instructor_id)
#     )
#     courses = result.all()

#     courses_list = [
#         {
#             "id": course.id,
#             "title": course.title,
#             "description": course.description,
#             "duration": course.duration,
#             "thumbnail": course.thumbnail,
#             "created_at": course.created_at.isoformat(),
#             "instructor_id": course.instructor_id,
#             "instructor_name": course.instructor_name
#         }
#         for course in courses
#     ]

#     return {
#         "status": "success",
#         "data": courses_list
#     }
################################
## Course GET method
#################################

# @router.get("/courses", tags=["courses"])
# async def get_all_courses(db: AsyncSession = Depends(get_session)):
#     # Join Course with User table to get instructor name
#     result = await db.execute(
#         select(
#             Course.id,
#             Course.title,
#             Course.description,
#             Course.duration,
#             Course.thumbnail,
#             Course.created_at,
#             Course.instructor_id,
#             User.name.label("instructor_name")
#         ).join(User, User.id == Course.instructor_id)
#     )
#     courses = result.all()

#     # Format data as list of dicts
#     courses_list = [
#         {
#             "id": course.id,
#             "title": course.title,
#             "description": course.description,
#             "duration": course.duration,
#             "thumbnail": course.thumbnail,
#             "created_at": course.created_at,
#             "instructor_id": course.instructor_id,
#             "instructor_name": course.instructor_name
#         }
#         for course in courses
#     ]

#     return {
#         "status": "success",
#         "data": courses_list
#     }


@router.get("/courses/{course_id}", tags=["courses"])
async def get_course_by_id(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(
            Course.id,
            Course.title,
            Course.description,
            Course.duration,
            Course.thumbnail,
            Course.created_at,
            Course.instructor_id,
            User.name.label("instructor_name")
        ).join(User, User.id == Course.instructor_id).where(Course.id == course_id)
    )
    course = result.first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course_data = {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "duration": course.duration,
        "thumbnail": course.thumbnail,
        "created_at": course.created_at,
        "instructor_id": course.instructor_id,
        "instructor_name": course.instructor_name
    }

    return {
        "status": "success",
        "data": course_data
    }