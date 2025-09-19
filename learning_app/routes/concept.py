from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime
from schemas.course import ConceptCreate

from database.db import get_session
from models.course import Lesson, Concept

router = APIRouter(prefix="/concepts", tags=["concepts"])

# Create Concept
@router.post("/add")
async def add_concept(
    lesson_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Check if lesson exists
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Handle file
    file_content = None
    if file:
        file_content = await file.read()

    new_concept = Concept(
        lesson_id=lesson.id,
        title=title,
        description=description,
        file_content=file_content,
        created_at=datetime.utcnow(),
    )

    db.add(new_concept)
    await db.commit()
    await db.refresh(new_concept)

    return {
        "status": "success",
        "message": "Concept added successfully",
        "data": {"concept_id": new_concept.id, "title": new_concept.title},
    }


# Get all concepts under a lesson
@router.get("/lesson/{lesson_id}")
async def get_concepts_by_lesson(lesson_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Concept).where(Concept.lesson_id == lesson_id))
    concepts = result.scalars().all()

    return {"status": "success", "data": concepts}


# Get concept by ID
@router.get("/{concept_id}")
async def get_concept(concept_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalars().first()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    return {"status": "success", "data": concept}
