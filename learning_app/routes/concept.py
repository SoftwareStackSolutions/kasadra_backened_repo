from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime
from schemas.course import ConceptCreate

from database.db import get_session
from models.course import Lesson, Concept

router = APIRouter()

# Create Concept
@router.post("/add", tags=["concepts"])
async def add_concept(
    instructor_id: int = Form(...),
    course_id: int = Form(...),
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
        instructor_id = instructor_id,
        course_id = course_id,
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
        "data": {"instructor_id": instructor_id, "course_id": course_id, "lesson_id": lesson.id, "concept_id": new_concept.id, "title": new_concept.title},
    }

#get all concepts
@router.get("/all", tags=["concepts"])
async def get_all_concepts(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Concept))
    concepts = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": concept.id,
                "instructor_id": concept.instructor_id,
                "course_id": concept.course_id,
                "lesson_id": concept.lesson_id,
                "concept_id": concept.id,
                "title": concept.title,
                "description": concept.description,
                "created_at": concept.created_at,
            }
            for concept in concepts
        ],
    }

# Get concept by ID
@router.get("/{concept_id}", tags=["concepts"])
async def get_concept(concept_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalars().first()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    return {
        "id": concept.id,
        "instructor_id": concept.instructor_id,
        "course_id": concept.course_id,
        "lesson_id": concept.lesson_id,
        "title": concept.title,
        "description": concept.description,
        "created_at": concept.created_at,
    }
