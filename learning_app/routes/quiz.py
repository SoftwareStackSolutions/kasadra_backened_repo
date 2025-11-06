from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from database.db import get_session
from models.course import Concept
from models.course import Quiz, Course, Lesson, Concept
from utils.gcp import upload_file_to_gcs

router = APIRouter()

# Create Quiz
@router.post("/add", tags=["quizzes"])
async def add_quiz(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    concept_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    quiz_link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),  # ✅ added file input
    db: AsyncSession = Depends(get_session),
):
    # ✅ Validate concept exists and matches course & lesson
    result = await db.execute(
        select(Concept).where(
            Concept.id == concept_id,
            Concept.lesson_id == lesson_id,
            Concept.course_id == course_id,
        )
    )
    concept = result.scalars().first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found for given course/lesson")

    # ✅ Upload file to S3 if provided
    file_url = None
    if file and file.filename:
        filename = f"quizzes/{course_id}/{lesson_id}/{concept_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        file_url = await upload_file_to_s3(file, filename)

    # ✅ Create Quiz record with file_url
    new_quiz = Quiz(
        course_id=course_id,
        lesson_id=lesson_id,
        concept_id=concept_id,
        title=title,
        description=description,
        quiz_link=quiz_link,
        file_url=file_url,  # ✅ store file URL
        created_at=datetime.utcnow(),
    )

    db.add(new_quiz)
    await db.commit()
    await db.refresh(new_quiz)

    return {
        "status": "success",
        "message": "Quiz added successfully",
        "data": {
            "quiz_id": new_quiz.id,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "concept_id": concept_id,
            "title": new_quiz.title,
            "quiz_link": new_quiz.quiz_link,
            "file_url": file_url,  # ✅ return file URL in response
        },
    }

# Get all quizzes for a concept
@router.get("/concept/{concept_id}", tags=["quizzes"])
async def get_quizzes_by_concept(concept_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Quiz).where(Quiz.concept_id == concept_id))
    quizzes = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": quiz.id,
                "course_id": quiz.course_id,
                "lesson_id": quiz.lesson_id,
                "concept_id": quiz.concept_id,
                "title": quiz.title,
                "description": quiz.description,
                "quiz_link": quiz.quiz_link,
                "created_at": quiz.created_at,
            }
            for quiz in quizzes
        ],
    }

@router.put("/update/{quiz_id}", tags=["quizzes"])
async def update_quiz(
    quiz_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    quiz_link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Fetch quiz
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Update text fields if provided
    if title and title.strip() not in ["", "string"]:
        quiz.title = title.strip()
    if description and description.strip() not in ["", "string"]:
        quiz.description = description.strip()
    if quiz_link and quiz_link.strip() not in ["", "string"]:
        quiz.quiz_link = quiz_link.strip()

    # Update file if a new one is uploaded
    if file and file.filename:
        filename = f"quizzes/{quiz.course_id}/{quiz.lesson_id}/{quiz.concept_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        quiz.file_url = await upload_file_to_s3(file, filename)

    # Save updates
    await db.commit()
    await db.refresh(quiz)

    return {
        "status": "success",
        "message": "Quiz updated successfully",
        "data": {
            "quiz_id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "quiz_link": quiz.quiz_link,
            "file_url": quiz.file_url,
        },
    }

@router.delete("/delete/{quiz_id}", tags=["quizzes"])
async def delete_quiz(quiz_id: int, db: AsyncSession = Depends(get_session)):
    # Fetch quiz
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Delete quiz record
    await db.delete(quiz)
    await db.commit()

    return {
        "status": "success",
        "message": f"Quiz with ID {quiz_id} deleted successfully"
    }
