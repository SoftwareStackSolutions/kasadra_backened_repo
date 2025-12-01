from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.course import Course, MeetingLink, Batch
from database.db import get_session
from models.user import User
from schemas.course import MeetingCreate, MeetingResponse

router = APIRouter()

################## Create Meeting Link #################

@router.post("/meeting-links", tags=["Meeting link"])
async def create_meeting_link(
    meeting_in: MeetingCreate,
    db: AsyncSession = Depends(get_session)
):
    instructor = await db.get(User, meeting_in.instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    course = await db.get(Course, meeting_in.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    batch = await db.get(Batch, meeting_in.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    meeting = MeetingLink(
        instructor_id=meeting_in.instructor_id,
        course_id=meeting_in.course_id,
        batch_id=meeting_in.batch_id,
        meeting_url=str(meeting_in.meeting_url)
    )

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    return {
        "id": meeting.id,
        "course_title": course.title,
        "batch_name": batch.batch_name,   
        "meeting_url": meeting.meeting_url
    }

################## Get Meeting Links by Instructor ID #################

@router.get("/meeting-links/{instructor_id}", tags=["Meeting link"])
async def get_meeting_links_by_instructor(
    instructor_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Fetch only the meeting links created by this instructor."""
    query = await db.execute(
        select(MeetingLink).where(MeetingLink.instructor_id == instructor_id)
    )
    meetings = query.scalars().all()

    if not meetings:
        return {
            "status": "success",
            "message": "No meeting links found for this instructor",
            "data": []
        }
    

    results = []
    for m in meetings:
        course = await db.get(Course, m.course_id)
        batch = await db.get(Batch, m.batch_id)

        results.append({
            "id": m.id,
            "course_id": m.course_id,       # added
            "batch_id": m.batch_id,         # added
            "course_title": course.title if course else None,
            "batch_name": batch.batch_name if batch else None,
            "meeting_url": m.meeting_url
        })

    return {
        "status": "success",
        "message": "Meeting links fetched successfully",
        "data": results
    }

################## Update Meeting Link #################

@router.put("/meeting-links/{meeting_id}", tags=["Meeting link"])
async def update_meeting_link(
    meeting_id: int,
    meeting_in: MeetingCreate,   # You can also make a separate Update schema if needed
    db: AsyncSession = Depends(get_session)
):
    # Fetch the meeting link
    meeting = await db.get(MeetingLink, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting link not found")

    # Ensure instructor is updating *their own* meeting link
    if meeting.instructor_id != meeting_in.instructor_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update this meeting link"
        )

    # Update allowed fields
    meeting.course_id = meeting_in.course_id
    meeting.batch_id = meeting_in.batch_id
    meeting.meeting_url = str(meeting_in.meeting_url)

    # Commit changes
    await db.commit()
    await db.refresh(meeting)

    # Fetch related info for clean response
    course = await db.get(Course, meeting.course_id)
    batch = await db.get(Batch, meeting.batch_id)

    return {
        "status": "success",
        "message": "Meeting link updated successfully",
        "data": {
            "id": meeting.id,
            "course_title": course.title if course else None,
            "batch_name": batch.batch_name if batch else None,
            "meeting_url": meeting.meeting_url
        }
    }

################## Delete Meeting Link #################

@router.delete("/meeting-links/{meeting_id}", tags=["Meeting link"])
async def delete_meeting_link(
    meeting_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Fetch meeting link
    meeting = await db.get(MeetingLink, meeting_id)

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting link not found"
        )

    # Delete the record
    await db.delete(meeting)
    await db.commit()

    return {
        "status": "success",
        "message": "Meeting link deleted successfully",
        "deleted_id": meeting_id
    }


################## Get Meeting Link for Student #################
# @router.get("/meeting-links/student/{student_id}/{batch_id}", tags=["Meeting link"])
# async def get_meeting_link_for_student(
#     student_id: int,
#     batch_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     """
#     Student view meeting link using student_id + batch_id.
#     """

#     #Check if student exists
#     student = await db.get(User, student_id)
#     if not student:
#         raise HTTPException(status_code=404, detail="Student not found")

#     #Check if batch exists
#     batch = await db.get(Batch, batch_id)
#     if not batch:
#         raise HTTPException(status_code=404, detail="Batch not found")

#     #Fetch the meeting link for that batch
#     query = await db.execute(
#         select(MeetingLink).where(MeetingLink.batch_id == batch_id)
#     )
#     meeting = query.scalars().first()

#     if not meeting:
#         return {
#             "status": "success",
#             "message": "No meeting link found for this batch",
#             "data": None
#         }

#     # Also fetch course data
#     course = await db.get(Course, meeting.course_id)

#     return {
#         "status": "success",
#         "message": "Meeting link fetched successfully",
#         "data": {
#             "meeting_id": meeting.id,
#             "course_id": meeting.course_id,
#             "course_title": course.title if course else None,
#             "batch_id": batch_id,
#             "batch_name": batch.batch_name,
#             "meeting_url": meeting.meeting_url
#         }
#     }

from models.user import User,RoleEnum
from models.course import BatchStudent

@router.get("/student/meeting/{student_id}/{course_id}", tags=["Meeting link"])
async def get_student_meeting(student_id: int, course_id: int, db: AsyncSession = Depends(get_session)):

    # 1. Validate student
    student = await db.get(User, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    if student.role != RoleEnum.student:
        raise HTTPException(403, "User is not a student")

    # 2. Find batch assigned to student
    mapping = (
        await db.execute(
            select(BatchStudent).where(BatchStudent.student_id == student_id)
        )
    ).scalar_one_or_none()

    if not mapping:
        raise HTTPException(404, "Student is not assigned to any batch")

    batch = await db.get(Batch, mapping.batch_id)

    # 3. Check batch matches the course
    if batch.course_id != course_id:
        raise HTTPException(400, "Student is not enrolled in this course")

    # 4. Fetch meeting for this batch (MAIN PART)
    meeting = (
        await db.execute(
            select(MeetingLink).where(MeetingLink.batch_id == batch.id)
        )
    ).scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "No meeting scheduled for this batch")
     # 5. Fetch course for course_name
    course = await db.get(Course, course_id)

    # 5. Final Response (NO CALENDAR!)
    return {
        "status": "success",
        "student_id": student_id,
        "course_id": course_id,
        "course_title": course.title if course else None,
        "batch_id": batch.id,
        "batch_name": batch.batch_name,
        "meeting_url": meeting.meeting_url
    }
