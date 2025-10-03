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
from typing import Optional
from sqlalchemy.orm import joinedload
from fastapi.staticfiles import StaticFiles
import os
from fastapi.responses import JSONResponse

from dependencies.auth_dep import get_current_user

router = APIRouter()

# ✅ Pydantic schema (for documentation / response)
class CourseResponse(BaseModel):
    course_id: int
    title: str
    instructor_id: int
    instructor_name: Optional[str]
    course_name: str

@router.post("/add", tags=["courses"], response_model=CourseResponse)
async def add_course(
    title: str = Form(...),
    description: str = Form(...),
    duration: str = Form(...),
    instructor_id: Optional[int] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    instructor_id = instructor_id or 1

    # ✅ Check if instructor exists
    result = await db.execute(select(User).where(User.id == instructor_id))
    instructor = result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"You are not an instructor"
        )

    # Save image to "uploads/" folder
    thumbnail_path = None
    if thumbnail:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        thumbnail_path = os.path.join(upload_dir, thumbnail.filename)

        with open(thumbnail_path, "wb") as buffer:
            buffer.write(await thumbnail.read())

    new_course = Course(
        instructor_id=instructor_id,
        title=title,
        description=description,
        duration=duration,
        thumbnail=thumbnail_path,
        created_at=datetime.utcnow()
    )

    db.add(new_course)
    await db.commit()
    await db.refresh(new_course, attribute_names=["instructor"])

    return {
        "course_id": new_course.id,
        "title": new_course.title,
        "instructor_id": new_course.instructor_id,
        "instructor_name": instructor.name,  # ✅ safe since instructor exists
        "course_name": new_course.title,
        "thumbnail_url": f"/uploads/{thumbnail.filename}" if thumbnail else None
    }


from sqlalchemy.orm import joinedload

@router.get("/all", tags=["courses"])
async def get_all_courses(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Course).options(joinedload(Course.instructor))
    )
    courses = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "id": course.id,
                "instructor_id": course.instructor_id,
                "instructor_name": course.instructor.name if course.instructor else None,
                "title": course.title,
                "description": course.description,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "created_at": course.created_at,
            }
            for course in courses
        ]
    }



@router.get("/{course_id}", tags=["courses"])
async def get_course_by_id(course_id: int, db: AsyncSession = Depends(get_session)):
    # Query course with instructor join
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
        )
        .join(User, User.id == Course.instructor_id)
        .where(Course.id == course_id)
    )
    course = result.first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {
        "status": "success",
        "data": {
                "id": course.id,
                "instructor_id": course.instructor_id,
                "instructor_name": course.instructor_name,
                "title": course.title,
                "description": course.description,
                "duration": course.duration,
                "thumbnail": course.thumbnail,
                "created_at": course.created_at,
           
        }
    }


# @router.post("/lessons/{lesson_id}/contents/add", tags=["contents"])
# async def add_content(
#     lesson_id: int,
#     lesson_title: str = Form(...),
#     concept_title: str = Form(...),
#     description: str = Form(None),
#     file: UploadFile = File(None),
#     db: AsyncSession = Depends(get_session)
# ):
#     # check if lesson exists
#     result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
#     lesson = result.scalars().first()
#     if not lesson:
#         raise HTTPException(status_code=404, detail="Lesson not found")

#     file_content = None
#     if file:
#         if file.content_type != "application/pdf":
#             raise HTTPException(status_code=400, detail="Only PDF files allowed")
#         file_content = await file.read()

#     new_content = Content(
#         lesson_id=lesson.id,
#         lesson_title=lesson_title,
#         concept_title=concept_title,
#         description=description,
#         file_content=file_content
#     )

#     db.add(new_content)
#     await db.commit()
#     await db.refresh(new_content)

#     return {
#         "status": "success",
#         "message": "Content added successfully",
#         "data": {"content_id": new_content.id, "concept_title": new_content.concept_title}
#     }

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


# @router.get("/courses/{course_id}", tags=["courses"])
# async def get_course_by_id(course_id: int, db: AsyncSession = Depends(get_session)):
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
#         ).join(User, User.id == Course.instructor_id).where(Course.id == course_id)
#     )
#     course = result.first()

#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     course_data = {
#         "id": course.id,
#         "title": course.title,
#         "description": course.description,
#         "duration": course.duration,
#         "thumbnail": course.thumbnail,
#         "created_at": course.created_at,
#         "instructor_id": course.instructor_id,
#         "instructor_name": course.instructor_name
#     }

#     return {
#         "status": "success",
#         "data": course_data
#     }