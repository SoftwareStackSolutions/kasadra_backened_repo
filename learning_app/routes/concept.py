from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from database.db import get_session
from models.course import Lesson, Concept
from utils.s3 import upload_file_to_s3  # Make sure this exists and works

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
    # 1️⃣ Check if lesson exists
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 2️⃣ Upload file to S3 if provided
    file_url = None
    if file:
        filename = f"concepts/{course_id}/{lesson_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        file_url = await upload_file_to_s3(file, filename)

    # 3️⃣ Create Concept entry
    new_concept = Concept(
        instructor_id=instructor_id,
        course_id=course_id,
        lesson_id=lesson.id,
        title=title,
        description=description,
        file_url=file_url,       # store S3 URL
        created_at=datetime.utcnow(),
    )

    db.add(new_concept)
    await db.commit()
    await db.refresh(new_concept)

    return {
        "status": "success",
        "message": "Concept added successfully",
        "data": {
            "concept_id": new_concept.id,
            "instructor_id": instructor_id,
            "course_id": course_id,
            "lesson_id": lesson.id,
            "title": new_concept.title,
            "file_url": file_url,  # return S3 URL
        },
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

@router.put("/update/{concept_id}", tags=["concepts"])
async def update_concept(
    concept_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),  # Only accept UploadFile or None
    db: AsyncSession = Depends(get_session),
):
    # 1️⃣ Fetch the concept
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # 2️⃣ Update fields if provided
    if title and title.strip() not in ["", "string"]:
        concept.title = title.strip()
    if description and description.strip() not in ["", "string"]:
        concept.description = description.strip()

    # 3️⃣ Update file only if a new file is uploaded
    if file and file.filename:
        filename = f"concepts/{concept.course_id}/{concept.lesson_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        concept.file_url = await upload_file_to_s3(file, filename)
    # If file is None → keep old file_url

    # 4️⃣ Commit and refresh
    await db.commit()
    await db.refresh(concept)

    return {
        "status": "success",
        "message": "Concept updated successfully",
        "data": {
            "concept_id": concept.id,
            "title": concept.title,
            "description": concept.description,
            "file_url": concept.file_url,
            "course_id": concept.course_id,
            "lesson_id": concept.lesson_id,
            "instructor_id": concept.instructor_id,
        },
    }

@router.delete("/delete/{concept_id}", tags=["concepts"])
async def delete_concept(
    concept_id: int,
    db: AsyncSession = Depends(get_session),
):
    # 1️⃣ Fetch the concept
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # 2️⃣ Delete the concept
    await db.delete(concept)
    await db.commit()

    # 3️⃣ Return minimal success response
    return {
        "status": "success",
        "message": f"Concept with ID {concept_id} deleted successfully"
    }