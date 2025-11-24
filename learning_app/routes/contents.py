from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import Course, Lesson, Pdf, WebLink, Quiz, Lab
from database.db import get_session
from utils.gcp import upload_file_to_gcs  


pdf_router = APIRouter(tags=["PDF"])
weblink_router = APIRouter(tags=["WebLink"])
quiz_router = APIRouter(tags=["Quiz"])  
lab_router = APIRouter(tags=["Lab"])
######### Upload PDF file ###########

@pdf_router.post("/add/pdf")
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

    # Verify that the lesson belongs to the given course
    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course"
        )

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

######### Update PDF file ###########

@pdf_router.put("/update/pdf/{pdf_id}")
async def update_pdf(
    pdf_id: int,
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    # Verify PDF
    pdf_entry = (
        await db.execute(select(Pdf).where(Pdf.id == pdf_id))
    ).scalar_one_or_none()
    if not pdf_entry:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Verify course
    course = (
        await db.execute(select(Course).where(Course.id == course_id))
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lesson = (
        await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course",
        )

    new_file_url = await upload_file_to_gcs(file, "pdfs")

    # Update DB entry
    pdf_entry.course_id = course_id
    pdf_entry.lesson_id = lesson_id
    pdf_entry.file_url = new_file_url

    await db.commit()
    await db.refresh(pdf_entry)

    return {
        "status": "success",
        "message": "PDF updated successfully",
        "data": {
            "pdf_id": pdf_entry.id,
            "file_url": new_file_url,
        },
    }

############# Delete PDF #############

@pdf_router.delete("/delete/pdf/{pdf_id}")
async def delete_pdf(
    pdf_id: int,
    db: AsyncSession = Depends(get_session)
):
    pdf_result = await db.execute(select(Pdf).where(Pdf.id == pdf_id))
    pdf_entry = pdf_result.scalar_one_or_none()

    if not pdf_entry:
        raise HTTPException(status_code=404, detail="PDF not found")

    await db.delete(pdf_entry)
    await db.commit()

    return {
        "status": "success",
        "message": "PDF deleted successfully",
    }

############# Add WebLink #############

@weblink_router.post("/add/weblink")
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

    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course"
        )

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


############# Update WebLink #############

@weblink_router.put("/update/weblink/{weblink_id}")
async def update_weblink(
    weblink_id: int,
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    link_url: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    # Verify WebLink
    weblink_entry = (
        await db.execute(select(WebLink).where(WebLink.id == weblink_id))
    ).scalar_one_or_none()
    if not weblink_entry:
        raise HTTPException(status_code=404, detail="WebLink not found")

    # Verify course
    course = (
        await db.execute(select(Course).where(Course.id == course_id))
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson = (
        await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Lesson must belong to the course
    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course",
        )

    # Update DB entry
    weblink_entry.course_id = course_id
    weblink_entry.lesson_id = lesson_id
    weblink_entry.link_url = link_url

    await db.commit()
    await db.refresh(weblink_entry)

    return {
        "status": "success",
        "message": "WebLink updated successfully",
        "data": {
            "weblink_id": weblink_entry.id,
            "link_url": link_url,
        },
    }


############# Delete WebLink #############

@weblink_router.delete("/delete/weblink/{weblink_id}")
async def delete_weblink(
    weblink_id: int,
    db: AsyncSession = Depends(get_session)
):
    weblink_result = await db.execute(select(WebLink).where(WebLink.id == weblink_id))
    weblink_entry = weblink_result.scalar_one_or_none()

    if not weblink_entry:
        raise HTTPException(status_code=404, detail="WebLink not found")

    await db.delete(weblink_entry)
    await db.commit()

    return {
        "status": "success",
        "message": "WebLink deleted successfully",
    }


############# Add Quiz #############

@quiz_router.post("/add/quiz")
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
    course = (
        await db.execute(select(Course).where(Course.id == course_id))
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson = (
        await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ✅ Verify lesson belongs to this course
    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course"
        )

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

############# quiz get by ID ##########
@quiz_router.get("/get/quiz/{quiz_id}")
async def get_quiz_by_id(
    quiz_id: int,
    db: AsyncSession = Depends(get_session),
):
    quiz = (
        await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    ).scalar_one_or_none()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return {
        "status": "success",
        "message": "Quiz fetched successfully",
        "data": {
            "quiz_id": quiz.id,
            "course_id": quiz.course_id,
            "lesson_id": quiz.lesson_id,
            "name": quiz.name,
            "description": quiz.description,
            "url": quiz.url,
            "file_url": quiz.file_url,
        },
    }


############# Update Quiz #############

@quiz_router.put("/update/quiz/{quiz_id}")
async def update_quiz(
    quiz_id: int,
    name: str = Form(...),
    description: str = Form(None),
    url: str = Form(...),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_session),
):
    quiz = (await db.execute(select(Quiz).where(Quiz.id == quiz_id))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Update ONLY if value is actually provided (and not default Swagger string)
    if name not in [None, "", "string"]:
        quiz.name = name

    if description not in [None, "", "string"]:
        quiz.description = description

    if url not in [None, "", "string"]:
        quiz.url = url

    if file:
        quiz.file_url = await upload_file_to_gcs(file, "quiz-files")

    await db.commit()
    await db.refresh(quiz)

    return {
        "status": "success",
        "message": "Quiz updated successfully",
        "data": {
            "quiz_id": quiz.id,
            "name": quiz.name,
            "description": quiz.description,
            "url": quiz.url,
            "file_url": quiz.file_url,
        },
    }

############# Delete Quiz #############

@quiz_router.delete("/delete/quiz/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_session),
):
    quiz = (await db.execute(select(Quiz).where(Quiz.id == quiz_id))).scalar_one_or_none()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    await db.delete(quiz)
    await db.commit()

    return {"status": "success", "message": "Quiz deleted"}

############# Add Lab #############

@lab_router.post("/add/lab")
async def add_lab(
    course_id: int = Form(...),
    lesson_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    url: str = Form(...),            # optional
    file: UploadFile = File(None),   # optional
    db: AsyncSession = Depends(get_session),
):
    # Verify course
    course = (
        await db.execute(select(Course).where(Course.id == course_id))
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify lesson
    lesson = (
        await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Verify lesson belongs to this course
    if lesson.course_id != course_id:
        raise HTTPException(
            status_code=400,
            detail="The given lesson does not belong to the specified course"
        )

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

############# Update Lab #############

@lab_router.put("/update/lab/{lab_id}")
async def update_lab(
    lab_id: int,
    name: str = Form(None),
    description: str = Form(None),
    url: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_session),
):
    # Fetch LAB record
    lab_entry = (
        await db.execute(select(Lab).where(Lab.id == lab_id))
    ).scalar_one_or_none()

    if not lab_entry:
        raise HTTPException(status_code=404, detail="Lab not found")

    # Update fields ONLY if value is provided AND not Swagger's default "string"
    if name not in [None, "", "string"]:
        lab_entry.name = name

    if description not in [None, "", "string"]:
        lab_entry.description = description

    if url not in [None, "", "string"]:
        lab_entry.url = url

    # File upload optional
    if file:
        lab_entry.file_url = await upload_file_to_gcs(file, "lab-files")

    await db.commit()
    await db.refresh(lab_entry)

    return {
        "status": "success",
        "message": "Lab updated successfully",
        "data": {
            "lab_id": lab_entry.id,
            "name": lab_entry.name,
            "description": lab_entry.description,
            "url": lab_entry.url,
            "file_url": lab_entry.file_url,
        },
    }

############# Delete Lab #############

@lab_router.delete("/delete/lab/{lab_id}")
async def delete_lab(
    lab_id: int,
    db: AsyncSession = Depends(get_session),
):
    lab = (await db.execute(select(Lab).where(Lab.id == lab_id))).scalar_one_or_none()

    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    await db.delete(lab)
    await db.commit()

    return {"status": "success", "message": "Lab deleted"}
