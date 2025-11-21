from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User, RoleEnum
from models.course import Course, Note, Lesson, BatchLessonActivation, Batch
from database.db import get_session
from datetime import datetime
from typing import Optional
from dependencies.auth_dep import get_current_user
from utils.gcp import upload_file_to_gcs
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from schemas.course import NoteCreate

from sqlalchemy import text


router = APIRouter()

@router.get("/batches/{batch_id}/lessons", tags=["lesson-activate"])
async def get_lessons_for_batch(batch_id: int, db: AsyncSession = Depends(get_session)):

    # 1. Check batch exists
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")

    # 2. Get course_id from batch
    course_id = batch.course_id

    # 3. Fetch lessons for that course + LEFT JOIN activation
    sql = """
    SELECT 
        l.id AS lesson_id,
        l.lesson_title AS title,
        l.description,
        COALESCE(a.id IS NOT NULL, FALSE) AS is_active,
        a.activated_at
    FROM lessons l
    LEFT JOIN batch_lesson_activation a
        ON l.id = a.lesson_id AND a.batch_id = :batch_id
    WHERE l.course_id = :course_id
    ORDER BY l.id;
"""

    result = await db.execute(
        text(sql), 
        {"batch_id": batch_id, "course_id": course_id}
    )

    lessons = [
        {
            "lesson_id": row.lesson_id,
            "title": row.title,
            "description": row.description,
            "is_active": row.is_active,
            "activated_at": row.activated_at,
        }
        for row in result
    ]

    return {"status": "success", "lessons": lessons}


@router.post("/batches/{batch_id}/lessons/{lesson_id}/activate", tags=["lesson-activate"])
async def activate_lesson(batch_id: int, lesson_id: int, db: AsyncSession = Depends(get_session)):

    # Validate batch
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")

    # Validate lesson
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    # Check lesson belongs to same course as batch
    if lesson.course_id != batch.course_id:
        raise HTTPException(400, "Lesson does not belong to batch's course")

    # Insert activation (idempotent)
    sql = """
        INSERT INTO batch_lesson_activation (batch_id, lesson_id)
        VALUES (:batch_id, :lesson_id)
        ON CONFLICT (batch_id, lesson_id) DO NOTHING;
    """

    await db.execute(text(sql), {"batch_id": batch_id, "lesson_id": lesson_id})
    await db.commit()

    return {
        "status": "success",
        "message": "Lesson activated",
        "lesson_id": lesson_id,
        "batch_id": batch_id,
        "is_active": True
    }


@router.post("/batches/{batch_id}/lessons/{lesson_id}/deactivate", tags=["lesson-activate"])
async def deactivate_lesson(
    batch_id: int, 
    lesson_id: int, 
    db: AsyncSession = Depends(get_session)
):
    # 1. Ensure batch exists
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")

    # 2. Ensure lesson exists
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    # 3. Ensure lesson belongs to the same course as batch
    if lesson.course_id != batch.course_id:
        raise HTTPException(400, "Lesson does not belong to this batch course")

    # 4. Delete activation row
    await db.execute(
        text("DELETE FROM batch_lesson_activation WHERE batch_id = :b AND lesson_id = :l"),
        {"b": batch_id, "l": lesson_id}
    )
    await db.commit()

    return {
        "status": "success",
        "message": "Lesson deactivated",
        "lesson_id": lesson_id,
        "batch_id": batch_id,
        "is_active": False
    }
