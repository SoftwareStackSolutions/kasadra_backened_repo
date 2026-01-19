from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User, RoleEnum
from models.course import Course, Lesson, Pdf, WebLink, Quiz, Lab, Note, BatchLessonActivation
from database.db import get_session
from datetime import datetime
from typing import Optional
from dependencies.auth_dep import get_current_user
from utils.gcp import upload_file_to_gcs 
from pydantic import BaseModel
from typing import Optional, Union
from sqlalchemy.orm import selectinload

class LessonUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

class LessonCreate(BaseModel):
    instructor_id: int
    course_id: int
    title: str
    description: Optional[str] = None

router = APIRouter(tags=["lessons"])

################# Create lesson ################

@router.post("/add", tags=["lessons"])
async def add_lesson(
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_session),
):
    # Verify instructor
    result = await db.execute(select(User).where(User.id == lesson_data.instructor_id))
    instructor = result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    if instructor.role != RoleEnum.instructor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an instructor")

    # Verify course
    result = await db.execute(select(Course).where(Course.id == lesson_data.course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if course.instructor_id != lesson_data.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course was not created by the provided instructor"
        )

    # Create lesson
    new_lesson = Lesson(
        instructor_id=lesson_data.instructor_id,
        course_id=course.id,
        lesson_title=lesson_data.title,
        description=lesson_data.description,
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
            "instructor_id": lesson_data.instructor_id,
            "course_id": course.id,
            "course_title": course.title,
            "title": new_lesson.lesson_title,
            "description": new_lesson.description,
        },
    }

################## Get lessons by lesson_id #################

@router.get("/{lesson_id}", tags=["lessons"])
async def get_lesson_by_id(
    lesson_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Fetch lesson
    result = await db.execute(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .order_by(Lesson.id.asc()) 
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found"
        )

    # Fetch PDFs
    pdfs_result = await db.execute(
        select(Pdf)
        .where(Pdf.lesson_id == lesson_id)
        .order_by(Pdf.id.asc())
    )
    pdfs = pdfs_result.scalars().all()

    # Fetch WebLinks
    weblinks_result = await db.execute(
        select(WebLink)
        .where(WebLink.lesson_id == lesson_id)
        .order_by(WebLink.id.asc())
    )
    weblinks = weblinks_result.scalars().all()

    # Fetch Quizzes
    quizzes_result = await db.execute(
        select(Quiz)
        .where(Quiz.lesson_id == lesson_id)
        .order_by(Quiz.id.asc())
    )
    quizzes = quizzes_result.scalars().all()

    # Fetch Labs
    labs_result = await db.execute(
        select(Lab)
        .where(Lab.lesson_id == lesson_id)
        .order_by(Lab.id.asc())
    )
    labs = labs_result.scalars().all()
    
    notes_result = await db.execute(
    select(Note)
    .where(Note.lesson_id == lesson_id)
    .order_by(Note.id.asc())
    )
    notes = notes_result.scalars().all()
    return {
        "status": "success",
        "data": {
            "lesson_id": lesson.id,
            "course_id": lesson.course_id,
            "instructor_id": lesson.instructor_id,
            "title": lesson.lesson_title,
            "description": lesson.description,
            "created_at": lesson.created_at,

            # Add all related content
            "pdfs": [
                {
                    "id": pdf.id,
                    "title": pdf.title,
                    "file_url": pdf.file_url
                }
                for pdf in pdfs
            ],
            "weblinks": [
                {
                    "id": link.id,
                    "title": link.title,
                    "url": link.link_url
                }
                for link in weblinks
            ],
            "quizzes": [
                {
                    "id": quiz.id,
                    "name": quiz.name,
                    "description": quiz.description,
                    "url": quiz.url,
                    "file_url": quiz.file_url
                }
                for quiz in quizzes
            ],
            "labs": [
                {
                    "id": lab.id,
                    "name": lab.name,
                    "description": lab.description,
                    "url": lab.url,
                    "file_url": lab.file_url
                }
                for lab in labs
            ],
            "notes": [
                {
                    "id": n.id,
                    "course_id": n.course_id,
                    "lesson_id": n.lesson_id,
                    "instructor_id": n.instructor_id,
                    "title": n.title,
                    "notes": n.notes
                }
                for n in notes
            ]  # Placeholder for notes if needed in future
        },
    }
###################### Get lessons by course_id #####################

# @router.get("/all/{course_id}", tags=["lessons"])
# async def get_lessons_by_course_id(
#     course_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     result = await db.execute(
#         select(Lesson).where(Lesson.course_id == course_id).options(selectinload(Lesson.course))
#     )
#     lessons = result.scalars().all()

#     if not lessons:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No lessons found for this course")

#     return {
#         "status": "success",
#         "course_id": course_id,
#         "lessons": [
#             {
#                 "lesson_id": l.id,
#                 "title": l.lesson_title,
#                 "course_title": l.course.title,
#                 "description": l.description,
#                 "created_at": l.created_at,
#             } for l in lessons
#         ]
#     }

@router.get("/all/{course_id}", tags=["lessons"])
async def get_lessons_by_course_id(
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.id.asc())
        .options(selectinload(Lesson.course))
    )
    lessons = result.scalars().all()

    if not lessons:
        return {
            "status": "success",
            "course_id": course_id,
            "message": "No lessons found for this course",
            "lessons": []
        }

    return {
        "status": "success",
        "course_id": course_id,
        "message": "Lessons fetched successfully",
        "lessons": [
            {
                "lesson_id": l.id,
                "title": l.lesson_title,
                "course_title": l.course.title,
                "description": l.description,
                "created_at": l.created_at,
            }
            for l in lessons
        ]
    }

######################## Update lesson #######################

@router.put("/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    if lesson_data.title:
        lesson.lesson_title = lesson_data.title
    if lesson_data.description:
        lesson.description = lesson_data.description

    lesson.updated_at = datetime.utcnow()

    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    return {
        "status": "success",
        "message": "Lesson updated successfully",
        "data": {
            "lesson_id": lesson.id,
            "title": lesson.lesson_title,
            "description": lesson.description,
        },
    }

################### Delete lesson ###################

@router.delete("/delete/{lesson_id}", tags=["lessons"])
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    await db.delete(lesson)
    await db.commit()

    return {"status": "success", "message": "Lesson deleted successfully"}


###################### Get Course Lessons With Full Content ########################################

@router.get("/courses/{course_id}/lessons/details", tags=["lessons"])
async def get_course_lessons_with_full_content(
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Validate course
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch lessons for the course
    lessons_result = await db.execute(
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.id.asc()) 
    )
    lessons = lessons_result.scalars().all()

    if not lessons:
        return {
            "status": "success",
            "course_id": course_id,
            "course_title": course.title,
            "lessons": []
        }

    response_lessons = []

    for lesson in lessons:
        # PDFs
        pdfs = (await db.execute(
            select(Pdf)
            .where(Pdf.lesson_id == lesson.id)
            .order_by(Pdf.id.asc())
        )).scalars().all()

        # WebLinks
        weblinks = (await db.execute(
            select(WebLink)
            .where(WebLink.lesson_id == lesson.id)
            .order_by(WebLink.id.asc())
        )).scalars().all()

        # Quizzes
        quizzes = (await db.execute(
            select(Quiz)
            .where(Quiz.lesson_id == lesson.id)
            .order_by(Quiz.id.asc())
        )).scalars().all()

        # Labs
        labs = (await db.execute(
            select(Lab)
            .where(Lab.lesson_id == lesson.id)
            .order_by(Lab.id.asc())
        )).scalars().all()

        # Notes
        notes = (await db.execute(
            select(Note)
            .where(Note.lesson_id == lesson.id)
            .order_by(Note.id.asc())
        )).scalars().all()

        response_lessons.append({
            "lesson_id": lesson.id,
            "lesson_title": lesson.lesson_title,
            "description": lesson.description,
            "created_at": lesson.created_at,

            "pdfs": [
                {
                    "id": pdf.id,
                    "title": pdf.title,
                    "file_url": pdf.file_url
                } for pdf in pdfs
            ],

            "weblinks": [
                {
                    "id": link.id,
                    "title": link.title,
                    "url": link.link_url
                } for link in weblinks
            ],

            "quizzes": [
                {
                    "id": quiz.id,
                    "name": quiz.name,
                    "description": quiz.description,
                    "url": quiz.url,
                    "file_url": quiz.file_url
                } for quiz in quizzes
            ],

            "labs": [
                {
                    "id": lab.id,
                    "name": lab.name,
                    "description": lab.description,
                    "url": lab.url,
                    "file_url": lab.file_url
                } for lab in labs
            ],

            "notes": [
                {
                    "id": note.id,
                    "title": note.title,
                    "notes": note.notes,
                    "instructor_id": note.instructor_id
                } for note in notes
            ]
        })

    return {
        "status": "success",
        "course_id": course_id,
        "course_title": course.title,
        "lessons": response_lessons
    }
