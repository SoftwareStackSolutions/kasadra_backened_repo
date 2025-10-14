from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User, RoleEnum
from models.course import Course
from database.db import get_session
from datetime import datetime
from typing import Optional
from dependencies.auth_dep import get_current_user
from utils.s3 import upload_file_to_s3 
from sqlalchemy.orm import joinedload


router = APIRouter()


class CourseResponse(BaseModel):
    course_id: int
    title: str
    instructor_id: int
    instructor_name: Optional[str]
    course_name: str
    thumbnail_url: Optional[str]  # return S3 URL instead of Base64

    class Config:
        orm_mode = True


@router.post("/add", tags=["courses"], response_model=CourseResponse)
async def add_course(
    title: str = Form(...),
    description: str = Form(...),
    duration: str = Form(...),
    instructor_id: int = Form(...),
    thumbnail: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Validate instructor
    result = await db.execute(select(User).where(User.id == instructor_id))
    instructor = result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if instructor.role != RoleEnum.instructor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an instructor")

    # Upload thumbnail to S3
    thumbnail_url = None
    if thumbnail:
        filename = f"courses/{datetime.utcnow().timestamp()}_{thumbnail.filename}"
        thumbnail_url = await upload_file_to_s3(thumbnail, filename)

    # Create new course
    new_course = Course(
        instructor_id=instructor_id,
        title=title,
        description=description,
        duration=duration,
        thumbnail_url=thumbnail_url,  # store URL instead of binary
        created_at=datetime.utcnow(),
    )

    db.add(new_course)
    await db.commit()
    await db.refresh(new_course, attribute_names=["instructor"])

    # Return course info with S3 URL
    return {
        "course_id": new_course.id,
        "title": new_course.title,
        "instructor_id": instructor.id,
        "instructor_name": instructor.name,
        "course_name": new_course.title,
        "thumbnail_url": thumbnail_url,
    }


# Get all courses
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
                "thumbnail": course.thumbnail_url,
                "created_at": course.created_at,
            }
            for course in courses
        ]
    }

# Get course by ID
@router.get("/{course_id}", tags=["courses"])
async def get_course_by_id(course_id: int, db: AsyncSession = Depends(get_session)):
    # Query course with instructor join
    result = await db.execute(
        select(
            Course.id,
            Course.title,
            Course.description,
            Course.duration,
            Course.thumbnail_url,
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
                "thumbnail": course.thumbnail_url,
                "created_at": course.created_at,
           
        }
    }
