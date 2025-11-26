from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, RoleEnum
from models.course import Lesson
from models.course import Course
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
from models.course import Batch, BatchStudent
from schemas.course import BatchCreate
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload


from dependencies.auth_dep import get_current_user

router = APIRouter()

@router.post("/add", tags=["batches"])
async def add_batch(batch: BatchCreate, db: AsyncSession = Depends(get_session)):
    # ✅ Validate course exists
    course = await db.get(Course, batch.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {batch.course_id} not found"
        )

    # ✅ Validate instructor exists
    instructor = await db.get(User, batch.instructor_id)
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instructor with id {batch.instructor_id} not found"
        )

    # ✅ Check if user has instructor role
    if instructor.role != RoleEnum.instructor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {batch.instructor_id} is not an instructor"
        )

    # ✅ Check if course belongs to instructor
    if course.instructor_id != batch.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don't have access to create this batch."
        )

    # ✅ Create new batch
    new_batch = Batch(
        course_id=batch.course_id,
        batch_name=batch.batch_name,
        num_students=batch.num_students,
        instructor_id=batch.instructor_id,
        timing=batch.timing,
        start_date=batch.start_date,
        end_date=batch.end_date,    
        created_at=datetime.utcnow()
    )

    db.add(new_batch)
    await db.commit()
    await db.refresh(new_batch)

    return {
        "status": "success",
        "message": "Batch created successfully",
        "data": {
            "batch_id": new_batch.id,
            "course_id": new_batch.course_id,
            "batch_name": new_batch.batch_name,
            "num_students": new_batch.num_students,
            "instructor_id": new_batch.instructor_id,
            "timing": new_batch.timing,
            "start_date": new_batch.start_date,
            "end_date": new_batch.end_date
        }
    }

@router.get("/by-course/{course_id}", tags=["batches"])
async def get_batches_by_course(
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # ✅ Validate course exists
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )

    # ✅ Query all batches for the given course_id
    result = await db.execute(
        select(Batch)
        .where(Batch.course_id == course_id)
        .options(joinedload(Batch.instructor), joinedload(Batch.course))
    )
    batches = result.scalars().all()

    if not batches:
        return {
            "status": "success",
            "message": f"No batches found for course {course_id}",
            "data": []
        }

    return {
        "status": "success",
        "data": [
            {
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
                "num_students": batch.num_students,
                "course_id": batch.course_id,
                "course_name": batch.course.title if batch.course else None,
                "instructor_id": batch.instructor_id,
                "instructor_name": batch.instructor.name if batch.instructor else None,
                "timing": batch.timing,
                "start_date": batch.start_date,
            }
            for batch in batches
        ]
    }


@router.get("/all/{course_id}", tags=["assign_batches"])
async def get_all_batches(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Batch)
        .options(joinedload(Batch.course), joinedload(Batch.instructor))
        .where(Batch.course_id == course_id)   # ✅ filter by course_id
    )
    batches = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "batch_id": batch.id,
                "course_name": batch.course.title if batch.course else None,
                "batch_name": batch.batch_name,
                "num_students": batch.num_students,
                "instructor_name": batch.instructor.name if batch.instructor else None,
                "timing": batch.timing,
                "start_date": batch.start_date,
            }
            for batch in batches
        ]
    }


####### Assign batches #########

@router.post("/assign", tags=["batches"])
async def assign_student_to_batch(
    student_id: int = Form(...),
    batch_id: int = Form(...),
    db: AsyncSession = Depends(get_session)
):

    # Validate student
    student = await db.get(User, student_id)
    if not student or student.role != RoleEnum.student:
        raise HTTPException(status_code=404, detail="Invalid student")

    # Validate batch
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Count assigned students
    assigned_students_count = await db.execute(
        select(BatchStudent).where(BatchStudent.batch_id == batch_id)
    )
    assigned_count = len(assigned_students_count.all())

    # Check if batch limit reached
    if assigned_count >= batch.num_students:
        raise HTTPException(
            status_code=400,
            detail=f"{batch.batch_name} is full. Limit: {batch.num_students} students."
        )

    # Check if student already assigned
    result = await db.execute(
        select(BatchStudent).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.student_id == student_id
        )
    )
    exists = result.scalar_one_or_none()

    if exists:
        return {
            "status": "success",
            "message": "Student is already assigned to this batch",
            "student_name": student.name,
            "batch_name": batch.batch_name,
        }

    # Assign student
    assignment = BatchStudent(student_id=student_id, batch_id=batch_id)
    db.add(assignment)
    await db.commit()

    return {
        "status": "success",
        "message": "Student assigned successfully to batch",
        "student_name": student.name,
        "batch_name": batch.batch_name,
        "assigned_count": assigned_count + 1,
        "capacity": batch.num_students
    }

