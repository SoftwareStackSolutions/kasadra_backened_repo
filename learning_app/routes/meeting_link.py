from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from sqlalchemy.orm import joinedload
from models.course import Course, MeetingLink, Batch
from database.db import get_session
from models.user import User
from schemas.course import MeetingCreate, MeetingResponse

router = APIRouter()


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


##########################################################################################################

# @router.post("/meeting-links",tags=["Meeting link"])
# async def add_meeting(
#     meeting_in: MeetingCreate,
#     current_user: User = Depends(role_required(RoleEnum.instructor, RoleEnum.superuser)),
#     db: AsyncSession = Depends(get_session)
# ):
#     # ensure instructor is using their own instructor_id (safer than passing instructor_id)
#     instructor_id = current_user.id

#     # validate course & batch
#     course = await db.get(Course, meeting_in.course_id)
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     batch = await db.get(Batch, meeting_in.batch_id)
#     if not batch:
#         raise HTTPException(status_code=404, detail="Batch not found")

#     # Optional: ensure the batch belongs to the course
#     if batch.course_id != course.id:
#         raise HTTPException(status_code=400, detail="Batch does not belong to the given course")

#     # create meeting link
#     meeting = MeetingLink(
#         instructor_id=instructor_id,
#         course_id=meeting_in.course_id,
#         batch_id=meeting_in.batch_id,
#         meeting_url=str(meeting_in.meeting_url)
#     )
#     # optional title
#     if meeting_in.meeting_title:
#         meeting.meeting_title = meeting_in.meeting_title

#     db.add(meeting)
#     await db.commit()
#     await db.refresh(meeting)
#     return meeting


# @router.get("/by-instructor", response_model=list[MeetingResponse])
# async def get_meetings_by_current_instructor(
#     current_user: User = Depends(role_required(RoleEnum.instructor, RoleEnum.superuser)),
#     db: AsyncSession = Depends(get_session)
# ):
#     stmt = select(MeetingLink).where(MeetingLink.instructor_id == current_user.id).options(
#         joinedload(MeetingLink.course), joinedload(MeetingLink.batch)
#     )
#     result = await db.execute(stmt)
#     meetings = result.scalars().all()
#     return meetings


# @router.get("/by-course-batch/{course_id}/{batch_id}", response_model=list[MeetingResponse])
# async def get_meetings_by_course_batch(course_id: int, batch_id: int, db: AsyncSession = Depends(get_session)):
#     stmt = select(MeetingLink).where(
#         MeetingLink.course_id == course_id,
#         MeetingLink.batch_id == batch_id
#     )
#     result = await db.execute(stmt)
#     meetings = result.scalars().all()
#     return meetings


# @router.delete("/{meeting_id}", status_code=204)
# async def delete_meeting(
#     meeting_id: int,
#     current_user: User = Depends(role_required(RoleEnum.instructor, RoleEnum.superuser)),
#     db: AsyncSession = Depends(get_session)
# ):
#     # only instructor who created it or superuser can delete
#     stmt = select(MeetingLink).where(MeetingLink.id == meeting_id)
#     result = await db.execute(stmt)
#     meeting = result.scalar_one_or_none()
#     if not meeting:
#         raise HTTPException(status_code=404, detail="Meeting not found")

#     if current_user.role != RoleEnum.superuser and meeting.instructor_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not allowed to delete this meeting")

#     await db.delete(meeting)
#     await db.commit()
#     return None
