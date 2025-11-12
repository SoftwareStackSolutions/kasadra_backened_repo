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



# ------------------ GET All the courses ------------------
# @router.get("/meeting-links", tags=["Meeting link"])
# async def get_all_meeting_links(db: AsyncSession = Depends(get_session)):
#     """Fetch all meeting links with course & batch names."""
#     query = await db.execute(select(MeetingLink))
#     meetings = query.scalars().all()

#     results = []
#     for m in meetings:
#         course = await db.get(Course, m.course_id)
#         batch = await db.get(Batch, m.batch_id)
#         instructor = await db.get(User, m.instructor_id)

#         results.append({
#             "id": m.id,
#             "course_title": course.title if course else None,
#             "batch_name": batch.batch_name if batch else None,
#             "instructor_name": instructor.name if instructor else None,
#             "meeting_url": m.meeting_url
#         })
#     return results


# ------------------ GET  instructor_id ------------------ 
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
            "course_title": course.title if course else None,
            "batch_name": batch.batch_name if batch else None,
            "meeting_url": m.meeting_url
        })

    return {
        "status": "success",
        "message": "Meeting links fetched successfully",
        "data": results
    }


##########################################################################################################


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
