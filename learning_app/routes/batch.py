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
from schemas.batch import AssignStudentsRequest
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import Form
from typing import Optional
from sqlalchemy.orm import selectinload
from models.course import Batch, BatchStudent
from schemas.course import BatchCreate
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from schemas.batch import AssignStudentsRequest


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

####### Assign batches #########

@router.post("/assign", tags=["batches"])
async def assign_students_to_batch(data: AssignStudentsRequest, db: AsyncSession = Depends(get_session)):

    batch = await db.get(Batch, data.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    assigned, moved, skipped = [], [], []

    for student_id in data.student_ids:

        # 🔥 Lookup using student_id + course_id to avoid overwriting other course assignments
        result = await db.execute(
            select(BatchStudent).where(
                BatchStudent.student_id == student_id,
                BatchStudent.course_id == batch.course_id
            )
        )

        existing_assignment = result.scalar_one_or_none()

        if existing_assignment:
            if existing_assignment.batch_id == data.batch_id:
                skipped.append(student_id)
            else:
                existing_assignment.batch_id = data.batch_id
                existing_assignment.batch_name = batch.batch_name
                moved.append(student_id)

        else:
            db.add(
                BatchStudent(
                    student_id=student_id,
                    batch_id=data.batch_id,
                    course_id=batch.course_id,   # 🔥 required
                    batch_name=batch.batch_name
                )
            )
            assigned.append(student_id)

    await db.commit()

    return {
        "status": "success",
        "batch": batch.batch_name,
        "new_assigned": assigned,
        "moved": moved,
        "already_in_same_batch": skipped
    }


######## update assigned students #########
@router.put("/update", tags=["batches"])
async def update_student_batch(
    data: AssignStudentsRequest,
    db: AsyncSession = Depends(get_session)
):

    batch_id = data.batch_id
    student_ids = data.student_ids

    # Validate batch
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    moved_students = []
    assigned_new = []

    for student_id in student_ids:

        # Fetch all batch assignments for the student
        result = await db.execute(
            select(BatchStudent).where(BatchStudent.student_id == student_id)
        )
        assignments = result.scalars().all()

        if not assignments:
            # Student not assigned anywhere, create a new record
            db.add(
                BatchStudent(
                    student_id=student_id,
                    batch_id=batch_id,
                    batch_name=batch.batch_name
                )
            )
            assigned_new.append(student_id)
        else:
            # Update the first record to new batch
            main_assignment = assignments[0]
            if main_assignment.batch_id != batch_id:
                main_assignment.batch_id = batch_id
                main_assignment.batch_name = batch.batch_name
                moved_students.append(student_id)

            # Delete all duplicate extra rows if any
            if len(assignments) > 1:
                for extra in assignments[1:]:
                    await db.delete(extra)

    await db.commit()

    return {
        "status": "success",
        "message": "Batch assignment updated successfully",
        "batch": batch.batch_name,
        "assigned_new": assigned_new,
        "moved_students": moved_students
    }
