from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.course import Lesson, Batch
from database.db import get_session
from dependencies.auth_dep import get_current_user
from sqlalchemy import text


router = APIRouter()

@router.get("/batches/{batch_id}/lessons", tags=["lesson-activate"])
async def get_lessons_for_batch(batch_id: int, db: AsyncSession = Depends(get_session)):

    # 1. Check batch exists
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")

    course_id = batch.course_id

    # 2. Updated SQL (JOIN courses table)
    sql = """
    SELECT 
        l.id AS lesson_id,
        l.lesson_title AS title,
        l.description,
        c.id AS course_id,
        c.title AS course_name,
        COALESCE(a.id IS NOT NULL, FALSE) AS is_active,
        a.activated_at
    FROM lessons l
    JOIN courses c ON l.course_id = c.id
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
            "course_id": row.course_id,
            "course_name": row.course_name,
            "is_active": row.is_active,
            "activated_at": row.activated_at,
        }
        for row in result
    ]

    return {"status": "success", "lessons": lessons}



####################################################
### Activate / Deactivate in one
####################################################

@router.post("/batches/{batch_id}/lessons/{lesson_id}/activate", tags=["lesson-activate"])
async def toggle_lesson_activation(
    batch_id: int,
    lesson_id: int,
    db: AsyncSession = Depends(get_session)
):

    # Validate batch
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Validate lesson
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Validate lesson belongs to batch course
    if lesson.course_id != batch.course_id:
        raise HTTPException(status_code=400, detail="Lesson does not belong to this batch course")

    # Check if activation exists
    result = await db.execute(
        text("SELECT * FROM batch_lesson_activation WHERE batch_id = :b AND lesson_id = :l"),
        {"b": batch_id, "l": lesson_id}
    )
    existing = result.fetchone()

    if existing:
        # Deactivate
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

    else:
        # Activate
        await db.execute(
            text("""
                INSERT INTO batch_lesson_activation (batch_id, lesson_id)
                VALUES (:batch_id, :lesson_id)
                ON CONFLICT (batch_id, lesson_id) DO NOTHING
            """),
            {"batch_id": batch_id, "lesson_id": lesson_id}
        )
        await db.commit()

        return {
            "status": "success",
            "message": "Lesson activated",
            "lesson_id": lesson_id,
            "batch_id": batch_id,
            "is_active": True
        }















# @router.post("/batches/{batch_id}/lessons/{lesson_id}/activate", tags=["lesson-activate"])
# async def activate_lesson(batch_id: int, lesson_id: int, db: AsyncSession = Depends(get_session)):

#     # Validate batch
#     batch = await db.get(Batch, batch_id)
#     if not batch:
#         raise HTTPException(404, "Batch not found")

#     # Validate lesson
#     lesson = await db.get(Lesson, lesson_id)
#     if not lesson:
#         raise HTTPException(404, "Lesson not found")

#     # Check lesson belongs to same course as batch
#     if lesson.course_id != batch.course_id:
#         raise HTTPException(400, "Lesson does not belong to batch's course")

#     # Insert activation (idempotent)
#     sql = """
#         INSERT INTO batch_lesson_activation (batch_id, lesson_id)
#         VALUES (:batch_id, :lesson_id)
#         ON CONFLICT (batch_id, lesson_id) DO NOTHING;
#     """

#     await db.execute(text(sql), {"batch_id": batch_id, "lesson_id": lesson_id})
#     await db.commit()

#     return {
#         "status": "success",
#         "message": "Lesson activated",
#         "lesson_id": lesson_id,
#         "batch_id": batch_id,
#         "is_active": True
#     }


# @router.post("/batches/{batch_id}/lessons/{lesson_id}/deactivate", tags=["lesson-activate"])
# async def deactivate_lesson(
#     batch_id: int, 
#     lesson_id: int, 
#     db: AsyncSession = Depends(get_session)
# ):
#     # 1. Ensure batch exists
#     batch = await db.get(Batch, batch_id)
#     if not batch:
#         raise HTTPException(404, "Batch not found")

#     # 2. Ensure lesson exists
#     lesson = await db.get(Lesson, lesson_id)
#     if not lesson:
#         raise HTTPException(404, "Lesson not found")

#     # 3. Ensure lesson belongs to the same course as batch
#     if lesson.course_id != batch.course_id:
#         raise HTTPException(400, "Lesson does not belong to this batch course")

#     # 4. Delete activation row
#     await db.execute(
#         text("DELETE FROM batch_lesson_activation WHERE batch_id = :b AND lesson_id = :l"),
#         {"b": batch_id, "l": lesson_id}
#     )
#     await db.commit()

#     return {
#         "status": "success",
#         "message": "Lesson deactivated",
#         "lesson_id": lesson_id,
#         "batch_id": batch_id,
#         "is_active": False
#     }


