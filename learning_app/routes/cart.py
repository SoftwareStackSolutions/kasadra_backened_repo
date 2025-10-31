from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.add_to_cart import Cart
from models.course import Course
from database.db import get_session

router = APIRouter()

############################################
# Add Course to Cart (no JWT)
############################################
@router.post("/{student_id}/{course_id}", tags=["cart"])
async def add_to_cart(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Check if course exists
    course = await db.get(Course, course_id)
    if not course:
        return {"status": "error", "error": "Course not found"}

    # Check if already in cart
    existing = await db.execute(
        select(Cart).where(Cart.course_id == course_id, Cart.student_id == student_id)
    )
    if existing.scalar_one_or_none():
        return {"status": "error", "error": "Course already in cart"}

    # Add course to cart
    new_item = Cart(student_id=student_id, course_id=course_id)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return {"status": "success", "message": "Course added to cart successfully"}



############################################
# View Cart
############################################

@router.get("/view/{student_id}", tags=["cart"])
async def view_cart(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Fetch all courses in the student's cart
    result = await db.execute(
        select(Course.id, Course.title, Course.duration)
        .join(Cart, Course.id == Cart.course_id)
        .where(Cart.student_id == student_id)
    )
    courses = result.all()  # list of Row objects

    if not courses:  # If no courses in cart
        return {"status": "success", "message": "Your cart is empty"}

    # Convert Row objects to dict
    data = [dict(c._mapping) for c in courses]

    return {
        "status": "success",
        "data": data
    }


############################################
# Remove Course from Cart
############################################

@router.delete("/remove/{student_id}/{course_id}", tags=["cart"])
async def remove_from_cart(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Cart).where(Cart.student_id == student_id, Cart.course_id == course_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        return {"status": "error", "error": "Course not found in cart"}

    await db.delete(item)
    await db.commit()
    return {"status": "success", "message": "Course removed from cart"}


###############################################################################
# recommended courses
#############################################################################


from sqlalchemy import not_
from models.purchased_courses import PurchasedCourse

# @router.get("/recommended/{student_id}", tags=["recommended courses"])
# async def recommended_courses(
#     student_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     # Step 1: Get all purchased course IDs for this student
#     result = await db.execute(
#         select(PurchasedCourse.course_id).where(PurchasedCourse.student_id == student_id)
#     )
#     purchased_course_ids = [row[0] for row in result.all()]

#     # Step 2: Select all courses NOT in purchased_course_ids
#     query = select(Course.id, Course.title, Course.duration, Course.thumbnail_url)
#     if purchased_course_ids:
#         query = query.where(not_(Course.id.in_(purchased_course_ids)))

#     result = await db.execute(query)
#     courses = result.all()

#     # Step 3: Convert to dict
#     data = [dict(c._mapping) for c in courses]

#     if not data:
#         return {"status": "success", "data": [], "message": "No recommended courses available"}

#     return {"status": "success", "data": data}

###############################################################################
# Owner Akhilesh
# recommended courses & Get all course
###############################################################################


@router.get("/recommended/{student_id}", tags=["recommended courses"])
async def recommended_courses(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Step 1: Get all purchased course IDs for this student
    result = await db.execute(
        select(PurchasedCourse.course_id).where(PurchasedCourse.student_id == student_id)
    )
    purchased_course_ids = [row[0] for row in result.all()]

    # Step 2: If no purchased courses → show all courses
    if not purchased_course_ids:
        result = await db.execute(select(Course.id, Course.title, Course.duration, Course.thumbnail_url))
        courses = result.all()
        data = [dict(c._mapping) for c in courses]
        return {
            "status": "success",
            "data": data,
            "message": "Showing all available courses (new user)"
        }

    # Step 3: Otherwise, show recommended (not purchased) courses
    query = select(Course.id, Course.title, Course.duration, Course.thumbnail_url).where(
        not_(Course.id.in_(purchased_course_ids))
    )

    result = await db.execute(query)
    courses = result.all()
    data = [dict(c._mapping) for c in courses]

    if not data:
        return {"status": "success", "data": [], "message": "No recommended courses available"}

    return {"status": "success", "data": data, "message": "Recommended courses for you"}