from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User, RoleEnum
from models.course import Course, Lesson, Concept, Quiz, Lab
from database.db import get_session
from datetime import datetime
from typing import Optional
from dependencies.auth_dep import get_current_user
from utils.s3 import upload_file_to_s3  # Make sure this utility is implemented

router = APIRouter()

@router.post("/add", tags=["lessons"])
async def add_lesson(
    instructor_id: int = Form(...),
    course_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Verify instructor
    result = await db.execute(select(User).where(User.id == instructor_id))
    instructor = result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    if instructor.role != RoleEnum.instructor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an instructor")

    #  Verify course
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Ensure the course was created by the instructor
    if course.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course was not created by the provided instructor"
        )

    # Upload file to S3 if provided
    file_url = None
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files allowed")
        filename = f"lessons/{course_id}/{datetime.utcnow().timestamp()}_{file.filename}"
        file_url = await upload_file_to_s3(file, filename)

    # Create lesson
    new_lesson = Lesson(
        instructor_id=instructor_id,
        course_id=course.id,
        title=title,
        description=description,
        file_url=file_url,  # store S3 URL
        created_at=datetime.utcnow(),
    )

    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)

    return {
        "status": "success",
        "message": "Lesson added successfully",
        "data": {
            "lesson_id": new_lesson.id,
            "instructor_id": instructor_id,
            "course_id": course.id,
            "title": new_lesson.title,
            "file_url": file_url,  # return S3 URL
        },
    }
from sqlalchemy.orm import selectinload

@router.get("{lesson_id}", tags=["lessons"])
async def get_lesson_by_id(lesson_id: int, db: AsyncSession = Depends(get_session)):
    # Fetch lesson
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Build nested data
    lesson_data = {
        "lesson_id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "file_url": lesson.file_url,
        "course_id": lesson.course_id,
        "created_at": lesson.created_at,
        "concepts": []
    }

    # Fetch concepts under this lesson
    result = await db.execute(select(Concept).where(Concept.lesson_id == lesson_id))
    concepts = result.scalars().all()

    for concept in concepts:
        # Fetch quizzes for this concept
        quiz_result = await db.execute(select(Quiz).where(Quiz.concept_id == concept.id))
        quizzes = quiz_result.scalars().all()

        # Fetch labs for this concept
        lab_result = await db.execute(select(Lab).where(Lab.concept_id == concept.id))
        labs = lab_result.scalars().all()

        concept_data = {
            "concept_id": concept.id,
            "title": concept.title,
            "description": concept.description,
            "file_url": concept.file_url,
            "created_at": concept.created_at,
            "quizzes": [
                {
                    "quiz_id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "quiz_link": quiz.quiz_link,
                    "created_at": quiz.created_at,
                }
                for quiz in quizzes
            ],
            "labs": [
                {
                    "lab_id": lab.id,
                    "title": lab.title,
                    "description": lab.description,
                    "file_url": lab.file_url,
                    "lab_link": lab.lab_link,
                    "created_at": lab.created_at,
                }
                for lab in labs
            ],
        }

        lesson_data["concepts"].append(concept_data)

    return {
        "status": "success",
        "data": lesson_data,
    }


@router.get("/all", tags=["lessons"])
async def get_all_lessons(db: AsyncSession = Depends(get_session)):
    from models.course import ScheduleClass  # import inside to avoid circular dependency

    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.course))
    )
    lessons = result.scalars().all()

    data = []
    for lesson in lessons:
        # Fetch the schedule for each lesson (if any)
        schedule_result = await db.execute(
            select(ScheduleClass)
            .where(ScheduleClass.lesson_id == lesson.id)
        )
        schedule = schedule_result.scalar_one_or_none()

        data.append({
            "id": lesson.id,
            "instructor_id": lesson.instructor_id,
            "course_name": lesson.course.title if lesson.course else None,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "description": lesson.description,
            "created_at": lesson.created_at,
            "session_date": schedule.session_date.strftime("%Y-%m-%d %H:%M") if schedule and schedule.session_date else None,
            "release_time": schedule.release_time if schedule and hasattr(schedule, "release_time") else "Not set",
            "status": "Scheduled" if schedule else "Not Scheduled"
        })

    return {
        "status": "success",
        "data": data
    }





@router.get("/all{course_id}", tags=["lessons"])
async def get_lessons_by_course(course_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.concepts).selectinload(Concept.quizzes),
                 selectinload(Lesson.concepts).selectinload(Concept.labs),
                 selectinload(Lesson.course))
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.created_at.desc())
    )
    lessons = result.scalars().all()

    if not lessons:
        return {"lessons": [], "message": "No lessons added yet"}

    lessons_response = [
        {
            "id": lesson.id,
            "lesson": lesson.title,
            "courseName": lesson.course.title if lesson.course else None,
            "sessionDate": lesson.created_at.strftime("%Y-%m-%d"),
            "releaseTime": None,
            "status": "Active",
            "concepts": [
                {
                    "id": concept.id,
                    "title": concept.title,
                    "quiz": len(concept.quizzes) > 0,
                    "lab": len(concept.labs) > 0,
                }
                for concept in lesson.concepts
            ],
        }
        for lesson in lessons
    ]

    return {"lessons": lessons_response}

