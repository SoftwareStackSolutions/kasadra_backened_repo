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
from models.course import Batch
from schemas.course import BatchCreate
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload


from dependencies.auth_dep import get_current_user

router = APIRouter()

@router.post("/add", tags=["batches"])
async def add_batch(batch: BatchCreate, db: AsyncSession = Depends(get_session)):
    new_batch = Batch(
        course_id=batch.course_id,
        batch_name=batch.batch_name,
        num_students=batch.num_students,
        instructor_id=batch.instructor_id,
        timing=batch.timing,
        start_date=batch.start_date,
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
        }
    }


@router.get("/all", tags=["batches"])
async def get_all_batches(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Batch).options(joinedload(Batch.course), joinedload(Batch.instructor)))
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
