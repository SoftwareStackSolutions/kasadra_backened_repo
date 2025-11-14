from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import Course, Lesson, Pdf, WebLink, Quiz, Lab
from database.db import get_session
from utils.gcp import upload_file_to_gcs  # Assuming you already have this util

router = APIRouter(tags=["contents"])


# ✅ Upload PDF file
@router.post("/add/pdf")
async def upload_pdf(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    # Verify course
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Upload file to GCP
    file_url = await upload_file_to_gcs(file, "pdfs")

    # Store entry in DB
    pdf_entry = Pdf(
        course_id=course_id,
        lesson_id=lesson_id,
        file_url=file_url,
    )

    db.add(pdf_entry)
    await db.commit()
    await db.refresh(pdf_entry)

    return {
        "status": "success",
        "message": "PDF uploaded successfully",
        "data": {
            "pdf_id": pdf_entry.id,
            "file_url": file_url,
        },
    }


# ✅ Add WebLink
@router.post("/add/weblink")
async def upload_weblink(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    link_url: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    # Verify course
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Store entry in DB
    weblink_entry = WebLink(
        course_id=course_id,
        lesson_id=lesson_id,
        link_url=link_url,
    )

    db.add(weblink_entry)
    await db.commit()
    await db.refresh(weblink_entry)

    return {
        "status": "success",
        "message": "Web link added successfully",
        "data": {
            "weblink_id": weblink_entry.id,
            "link_url": link_url,
        },
    }

@router.post("/add/quiz")
async def add_quiz(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    url: str = Form(...),             # optional
    file: UploadFile = File(None),    # optional
    db: AsyncSession = Depends(get_session),
):
    # Verify course
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Upload file if provided
    file_url = None
    if file:
        file_url = await upload_file_to_gcs(file, "quiz-files")

    # Save quiz entry
    quiz_entry = Quiz(
        course_id=course_id,
        lesson_id=lesson_id,
        name=name,
        description=description,
        url=url,
        file_url=file_url,
    )

    db.add(quiz_entry)
    await db.commit()
    await db.refresh(quiz_entry)

    return {
        "status": "success",
        "message": "Quiz added successfully",
        "data": {
            "quiz_id": quiz_entry.id,
            "name": name,
            "description": description,
            "url": url,
            "file_url": file_url,
        },
    }

@router.post("/add/lab")
async def add_lab(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None), 
    url: str = Form(...),           # optional
    file: UploadFile = File(None),   # optional
    db: AsyncSession = Depends(get_session),
):
    # Verify course
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Upload file if provided
    file_url = None
    if file:
        file_url = await upload_file_to_gcs(file, "lab-files")

    # Save lab entry
    lab_entry = Lab(
        course_id=course_id,
        lesson_id=lesson_id,
        name=name,
        description=description,
        url=url,
        file_url=file_url,
    )

    db.add(lab_entry)
    await db.commit()
    await db.refresh(lab_entry)

    return {
        "status": "success",
        "message": "Lab added successfully",
        "data": {
            "lab_id": lab_entry.id,
            "name": name,
            "description": description,
            "url": url,
            "file_url": file_url,
        },
    }
