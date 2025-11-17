from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User, RoleEnum
from models.course import Course, Note, Lesson
from database.db import get_session
from datetime import datetime
from typing import Optional
from dependencies.auth_dep import get_current_user
from utils.gcp import upload_file_to_gcs
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from models.purchased_courses import PurchasedCourse
from schemas.course import NoteCreate
# from models.instructor import Instructor

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
        thumbnail_url = await upload_file_to_gcs(thumbnail, filename)

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
    # Step 1: Get all courses with instructor data
    result = await db.execute(
        select(Course).options(joinedload(Course.instructor))
    )
    courses = result.scalars().all()

    # Step 2: Get enrollment count for each course
    enroll_result = await db.execute(
        select(
            PurchasedCourse.course_id,
            func.count(PurchasedCourse.id).label("enrollments")
        ).group_by(PurchasedCourse.course_id)
    )
    enrollments_data = {row.course_id: row.enrollments for row in enroll_result.all()}

    # Step 3: Combine both datasets
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
                "total_enrollments": enrollments_data.get(course.id, 0)  # ✅ Added here
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



@router.delete("/delete/{course_id}", tags=["courses"])
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_session),
):
    # 1️⃣ Fetch the course
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2️⃣ Delete the course
    await db.delete(course)
    await db.commit()

    # 3️⃣ Return minimal success response
    return {
        "status": "success",
        "message": f"Course with ID {course_id} deleted successfully"
    }

#################################################
## NOTES Post API
#################################################

@router.post("/notes", tags=["Notes"])
async def create_note(note_in: NoteCreate, db: AsyncSession = Depends(get_session)):

    # 1️⃣ Validate instructor (using User table)
    result = await db.execute(
        select(User).where(User.id == note_in.instructor_id)
    )
    instructor = result.scalar_one_or_none()

    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if instructor.role != RoleEnum.instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an instructor"
        )

    # 2️⃣ Validate course exists
    course = await db.get(Course, note_in.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # 3️⃣ Validate lesson exists
    lesson = await db.get(Lesson, note_in.lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # 4️⃣ Create note
    new_note = Note(
        course_id=note_in.course_id,
        lesson_id=note_in.lesson_id,
        instructor_id=note_in.instructor_id,
        notes=note_in.notes
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return {
        "status": "success",
        "message": "Note created successfully",
        "data": {
            "id": new_note.id,
            "course_id": new_note.course_id,
            "lesson_id": new_note.lesson_id,
            "instructor_id": new_note.instructor_id,
            "notes": new_note.notes
        }
    }
