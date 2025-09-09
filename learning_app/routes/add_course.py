from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, RoleEnum
from models.course import Course
from database.db import get_session
# from utils.auth import get_current_user
from datetime import datetime
from models.user import User
from sqlalchemy.future import select



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


@router.get("/courses", tags=["courses"])
async def get_all_courses(db: AsyncSession = Depends(get_session)):
    # Join Course with User table to get instructor name
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
        ).join(User, User.id == Course.instructor_id)
    )
    courses = result.all()

    # Format data as list of dicts
    courses_list = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "duration": course.duration,
            "thumbnail": course.thumbnail,
            "created_at": course.created_at,
            "instructor_id": course.instructor_id,
            "instructor_name": course.instructor_name
        }
        for course in courses
    ]

    return {
        "status": "success",
        "data": courses_list
    }


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




