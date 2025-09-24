from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from database.db import get_session
from models.course import Course, Lesson, Concept, Lab
from routes import course, lessons, concept

router = APIRouter()


# Create Lab
@router.post("/add", tags=["labs"])
async def add_lab(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    concept_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    lab_link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Check if concept exists
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalars().first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    file_content = await file.read() if file else None

    new_lab = Lab(
        course_id=concept.course_id,
        lesson_id=concept.lesson_id,
        concept_id=concept_id,
        title=title,
        description=description,
        file_content=file_content,
        lab_link=lab_link,
        created_at=datetime.utcnow(),
    )

    db.add(new_lab)
    await db.commit()
    await db.refresh(new_lab)

    return {
        "status": "success",
        "message": "Lab added successfully",
        "data": {
            "lab_id": new_lab.id,
            "concept_id": concept_id,
            "title": new_lab.title,
            "lab_link": new_lab.lab_link,
        },
    }

# Get all labs for a concept
@router.get("/concept/{lab_id}", tags=["labs"])
async def get_labs_by_concept(concept_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Lab).where(Lab.concept_id == concept_id))
    labs = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": lab.id,
                "concept_id": lab.concept_id,
                "title": lab.title,
                "description": lab.description,
                "lab_link": lab.lab_link,
                "created_at": lab.created_at,
            }
            for lab in labs
        ],
    }