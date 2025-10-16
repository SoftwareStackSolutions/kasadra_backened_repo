from models.purchased_courses import PurchasedCourse
from models.add_to_cart import Cart
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.add_to_cart import Cart
from models.course import Course
from database.db import get_session

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
    # Step 1: Check if course exists in cart
    result = await db.execute(
        select(Cart).where(Cart.student_id == student_id, Cart.course_id == course_id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        return {"status": "error", "error": "Course not found in cart"}

    # Step 2: Remove from cart
    await db.delete(cart_item)

    # Step 3: Add to purchased courses
    purchased = PurchasedCourse(student_id=student_id, course_id=course_id)
    db.add(purchased)

    await db.commit()

    return {"status": "success", "message": "Course purchased successfully"}


@router.get("/purchased/{student_id}", tags=["purchased"])
async def view_purchased_courses(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Course.id, Course.title, Course.duration)
        .join(PurchasedCourse, Course.id == PurchasedCourse.course_id)
        .where(PurchasedCourse.student_id == student_id)
    )
    courses = result.all()
    data = [dict(c._mapping) for c in courses]

    if not data:
        return {"status": "success", "data": [], "message": "No purchased courses yet"}

    return {"status": "success", "data": data}

