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
# 👀 View Cart
############################################

@router.get("/view/{student_id}", tags=["cart"])
async def view_cart(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Course.id, Course.title, Course.description, Course.thumbnail_url)
        .join(Cart, Course.id == Cart.course_id)
        .where(Cart.student_id == student_id)
    )

    courses = result.all()
    return {
        "status": "success",
        "data": [dict(c) for c in courses]
    }


############################################
# ❌ Remove Course from Cart
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
        raise HTTPException(status_code=404, detail="Course not found in cart")

    await db.delete(item)
    await db.commit()
    return {"status": "success", "message": "Course removed from cart"}


############################################
# 💳 Buy Course (move from cart to “purchased”)
############################################
@router.post("/buy/{student_id}/{course_id}", tags=["cart"])
async def buy_course(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Step 1: Remove from cart
    result = await db.execute(
        select(Cart).where(Cart.student_id == student_id, Cart.course_id == course_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Course not found in cart")

    await db.delete(item)
    await db.commit()

    # Step 2: Later, add to Purchased table if needed
    return {"status": "success", "message": "Course purchased successfully"}
