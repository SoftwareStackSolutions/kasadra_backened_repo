from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from database.db import get_session
from models.course import Concept
from models.course import Quiz, Course, Lesson

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
    db: AsyncSession = Depends(get_session),
):
    # Validate concept exists and matches course & lesson
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

    new_quiz = Quiz(
        course_id=course_id,
        lesson_id=lesson_id,
        concept_id=concept_id,
        title=title,
        description=description,
        quiz_link=quiz_link,
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