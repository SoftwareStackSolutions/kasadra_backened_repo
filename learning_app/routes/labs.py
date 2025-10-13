from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from database.db import get_session
from models.course import Course, Lesson, Concept, Lab
from utils.s3 import upload_file_to_s3  # Make sure this is implemented

router = APIRouter()


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
    # Check if course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if lesson exists
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if concept exists
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Upload file to S3 if provided
    file_url = None
    if file:
        filename = f"labs/{course_id}/{lesson_id}/{concept_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        file_url = await upload_file_to_s3(file, filename)

    # Create Lab entry
    new_lab = Lab(
        course_id=course_id,
        lesson_id=lesson_id,
        concept_id=concept_id,
        title=title,
        description=description,
        file_url=file_url,       # store S3 URL
        lab_link=lab_link,       # optional manual link
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
            "file_url": file_url,  
            "lab_link": lab_link,
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