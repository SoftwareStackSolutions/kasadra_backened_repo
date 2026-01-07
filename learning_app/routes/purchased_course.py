from models.purchased_courses import PurchasedCourse
from models.add_to_cart import Cart
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.add_to_cart import Cart
from models.course import User, Course
from models.course import Batch, BatchStudent
from database.db import get_session
from sqlalchemy import select, func, not_
from sqlalchemy.orm import joinedload
from fastapi import Depends, APIRouter
from models.purchased_courses import AssignedCourse


router = APIRouter()


############################################
# Buy Course 
############################################

@router.post("/{student_id}/{course_id}", tags=["purchased"])
async def buy_course(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Check if course exists in cart
    result = await db.execute(
        select(Cart).where(Cart.student_id == student_id, Cart.course_id == course_id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        return {"status": "error", "error": "Course not found in cart"}

    # Remove from cart
    await db.delete(cart_item)

    # Add to purchased courses
    purchased = PurchasedCourse(student_id=student_id, course_id=course_id)
    db.add(purchased)

    await db.commit()

    return {"status": "success", "message": "Course purchased successfully"}




@router.get("/all/{student_id}", tags=["recommended-ak"])
async def get_courses(student_id: int, db: AsyncSession = Depends(get_session)):
    # Step 1: Get all purchased course IDs for this student
    result = await db.execute(
        select(PurchasedCourse.course_id).where(PurchasedCourse.student_id == student_id)
    )
    purchased_course_ids = [row[0] for row in result.all()]

    # Step 2: Prepare base query (with instructor info)
    query = select(Course).options(joinedload(Course.instructor))

    # Step 3: If user has purchased courses → show only recommended (not purchased)
    if purchased_course_ids:
        query = query.where(not_(Course.id.in_(purchased_course_ids)))

    # Step 4: Fetch all selected courses
    result = await db.execute(query)
    courses = result.scalars().all()

    # Step 5: Get enrollment count for each course
    enroll_result = await db.execute(
        select(
            PurchasedCourse.course_id,
            func.count(PurchasedCourse.id).label("enrollments")
        ).group_by(PurchasedCourse.course_id)
    )
    enrollments_data = {row.course_id: row.enrollments for row in enroll_result.all()}

    # Step 6: Build response
    data = [
        {
            "id": course.id,
            "instructor_id": course.instructor_id,
            "instructor_name": course.instructor.name if course.instructor else None,
            "title": course.title,
            "description": course.description,
            "duration": course.duration,
            "thumbnail": course.thumbnail_url,
            "created_at": course.created_at,
            "total_enrollments": enrollments_data.get(course.id, 0)
        }
        for course in courses
    ]

    # Step 7: Return appropriate message
    if not purchased_course_ids:
        message = "Showing all available courses (new user)"
    elif not data:
        message = "No recommended courses available"
    else:
        message = "Showing recommended courses"

    return {"status": "success", "data": data, "message": message}


# @router.get("/courses/{student_id}", tags=["recommand"])
# async def get_all_courses_for_student(student_id: int, db: AsyncSession = Depends(get_session)):
#     # Step 1: Fetch all purchased course IDs for this student
#     result = await db.execute(
#         select(PurchasedCourse.course_id).where(PurchasedCourse.student_id == student_id)
#     )
#     purchased_course_ids = [row[0] for row in result.all()]

#     # Step 2: Prepare base query with instructor info
#     base_query = select(Course).options(joinedload(Course.instructor))

#     # Step 3: Get purchased courses (if any)
#     purchased_courses = []
#     if purchased_course_ids:
#         purchased_query = base_query.where(Course.id.in_(purchased_course_ids))
#         purchased_result = await db.execute(purchased_query)
#         purchased_courses = purchased_result.scalars().all()

#     # Step 4: Get recommended (not purchased) courses
#     recommended_query = base_query
#     if purchased_course_ids:
#         recommended_query = recommended_query.where(not_(Course.id.in_(purchased_course_ids)))

#     recommended_result = await db.execute(recommended_query)
#     recommended_courses = recommended_result.scalars().all()

#     # Step 5: Get enrollment counts for all courses
#     enroll_result = await db.execute(
#         select(
#             PurchasedCourse.course_id,
#             func.count(PurchasedCourse.id).label("enrollments")
#         ).group_by(PurchasedCourse.course_id)
#     )
#     enrollments_data = {row.course_id: row.enrollments for row in enroll_result.all()}

#     # Step 6: Format data
#     def serialize_course(course):
#         return {
#             "id": course.id,
#             "title": course.title,
#             "description": course.description,
#             "duration": course.duration,
#             "thumbnail": course.thumbnail_url,
#             "instructor_id": course.instructor_id,
#             "instructor_name": course.instructor.name if course.instructor else None,
#             "created_at": course.created_at,
#             "total_enrollments": enrollments_data.get(course.id, 0)
#         }

#     purchased_data = [serialize_course(c) for c in purchased_courses]
#     recommended_data = [serialize_course(c) for c in recommended_courses]

#     # Step 7: Message logic
#     if not purchased_course_ids:
#         message = "Showing all available courses (new user)"
#     elif not recommended_data:
#         message = "All courses purchased"
#     else:
#         message = "Showing purchased and recommended courses"

#     # Step 8: Return response
#     return {
#         "status": "success",
#         "message": message,
#         "purchased_courses": purchased_data,
#         "recommended_courses": recommended_data
#     }


############################################
# Owner Akhilesh
# Devlopment date : 07-01-2026 
# Purpose : The course can be purchased by the user +  Manually assigned by the instructor 
# UI design : My course
############################################


@router.get("/courses/{student_id}", tags=["recommand"])
async def get_all_courses_for_student(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    # -------------------------------
    # 1. Purchased course IDs
    # -------------------------------
    result = await db.execute(
        select(PurchasedCourse.course_id)
        .where(PurchasedCourse.student_id == student_id)
    )
    purchased_course_ids = {row[0] for row in result.all()}

    # -------------------------------
    # 2. Assigned course IDs
    # -------------------------------
    result = await db.execute(
        select(AssignedCourse.course_id)
        .where(AssignedCourse.student_id == student_id)
    )
    assigned_course_ids = {row[0] for row in result.all()}

    # -------------------------------
    # 3. Accessible courses (union)
    # -------------------------------
    accessible_course_ids = purchased_course_ids | assigned_course_ids

    base_query = select(Course).options(joinedload(Course.instructor))

    # -------------------------------
    # 4. My Courses (Purchased + Assigned)
    # -------------------------------
    my_courses = []
    if accessible_course_ids:
        my_query = base_query.where(Course.id.in_(accessible_course_ids))
        result = await db.execute(my_query)
        my_courses = result.scalars().all()

    # -------------------------------
    # 5. Recommended Courses
    # -------------------------------
    recommended_query = base_query
    if accessible_course_ids:
        recommended_query = recommended_query.where(
            not_(Course.id.in_(accessible_course_ids))
        )

    result = await db.execute(recommended_query)
    recommended_courses = result.scalars().all()

    # -------------------------------
    # 6. Enrollment counts (Purchased only)
    # -------------------------------
    enroll_result = await db.execute(
        select(
            PurchasedCourse.course_id,
            func.count(PurchasedCourse.id).label("enrollments")
        ).group_by(PurchasedCourse.course_id)
    )
    enrollments = {row.course_id: row.enrollments for row in enroll_result.all()}

    # -------------------------------
    # 7. Serializer
    # -------------------------------
    def serialize_course(course):
        access_type = "assigned"
        if course.id in purchased_course_ids:
            access_type = "purchased"

        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "duration": course.duration,
            "thumbnail": course.thumbnail_url,
            "instructor_id": course.instructor_id,
            "instructor_name": course.instructor.name if course.instructor else None,
            "created_at": course.created_at,
            "total_enrollments": enrollments.get(course.id, 0),
            "access_type": access_type
        }

    my_courses_data = [serialize_course(c) for c in my_courses]
    recommended_data = [serialize_course(c) for c in recommended_courses]

    # -------------------------------
    # 8. Message logic
    # -------------------------------
    if not my_courses_data:
        message = "No courses assigned or purchased yet"
    elif not recommended_data:
        message = "All available courses are already in your account"
    else:
        message = "Showing your courses and recommendations"

    # -------------------------------
    # 9. Response
    # -------------------------------
    return {
        "status": "success",
        "message": message,
        "my_courses": my_courses_data,
        "recommended_courses": recommended_data
    }


######### get students list by course ID ########3

@router.get("/course/{course_id}/students", tags=["purchased"])
async def get_students_by_course(course_id: int, db: AsyncSession = Depends(get_session)):

    # Validate course exists
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        select(
            User.id.label("student_id"),
            User.name,
            User.email,
            PurchasedCourse.purchased_at,
            Batch.batch_name,
        )
        .join(PurchasedCourse, PurchasedCourse.student_id == User.id)
        .outerjoin(
            BatchStudent, 
            (BatchStudent.student_id == User.id) & 
            (BatchStudent.course_id == course_id)  
        )
        .outerjoin(Batch, Batch.id == BatchStudent.batch_id)
        .where(PurchasedCourse.course_id == course_id)
    )

    result = await db.execute(query)
    records = result.mappings().all()

    # Deduplicate logic (already good)
    student_map = {}
    for row in records:
        sid = row["student_id"]

        if sid not in student_map:
            student_map[sid] = {
                "student_id": sid,
                "name": row["name"],
                "email": row["email"],
                "purchased_at": row["purchased_at"],
                "batch_name": row["batch_name"],
                "status": "Assigned" if row["batch_name"] else "Unassigned",
            }
        else:
            if student_map[sid]["batch_name"] is None and row["batch_name"] is not None:
                student_map[sid]["batch_name"] = row["batch_name"]
                student_map[sid]["status"] = "Assigned"

    return {
        "status": "success",
        "course_id": course_id,
        "total_students": len(student_map),
        "students": list(student_map.values())
    }