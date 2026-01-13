from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, constr
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.passwd import hash_password, verify_password
from models.user import User, RoleEnum
from database.db import get_session
from common import get_user_by_email
from utils.auth import create_access_token
from datetime import timedelta
from dependencies.auth_dep import get_current_user
from utils.passwd import hash_password, verify_password
from passlib.context import CryptContext    

from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation 
import re
from datetime import datetime, date

from models.course import Course
from models.purchased_courses import PurchasedCourse
from models.purchased_courses import AssignedCourse
router = APIRouter()

MAX_BCRYPT_PASSWORD_BYTES = 72

# --------------------------
# Pydantic schema
# --------------------------
class StudentCreate(BaseModel):
    Name: str
    Email: EmailStr
    PhoneNo: str = Field(..., alias="Phone No")
    Password: str
    created_at: date
    Confirmpassword: str = Field(..., alias="Confirm Password")


    @field_validator("PhoneNo")
    @classmethod
    def validate_phone(cls, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be 10 digits")
        return value

    @model_validator(mode="after")
    def check_passwords(self):
        # Check password match
        if self.Password != self.Confirmpassword:
            raise ValueError("Passwords do not match")

        # Truncate to bcrypt max bytes
        password_bytes = self.Password.encode("utf-8")
        if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
            truncated = password_bytes[:MAX_BCRYPT_PASSWORD_BYTES].decode("utf-8", errors="ignore")
            object.__setattr__(self, "Password", truncated)

        return self

    model_config = {"populate_by_name": True}


class LoginRequestDetails(BaseModel):
    Email: EmailStr
    Password: str

##############################
## Create Students 
##############################

@router.post("/create", tags=["students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_session)):
    try:
        # Check if email exists
        student_exists = await get_user_by_email(student.Email, db)
        if student_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": "Email already registered", "data": {}}
            )

        # Hash password safely
        hashed_password = hash_password(student.Password)

        # Create new student
        new_student = User(
            name=student.Name,
            email=student.Email,
            phone_no=student.PhoneNo,
            password=hashed_password,
            role=RoleEnum.student
        )

        db.add(new_student)
        await db.commit()
        await db.refresh(new_student)

        return {
            "detail": {
                "status": "success",
                "message": "Student created successfully",
                "data": {"id": new_student.id}
            }
        }

    except IntegrityError as e:
        await db.rollback()
        if "users_phone_no_key" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": "Phone number already exists", "data": {}}
            )
        raise

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Failed to create student: {str(e)}", "data": {}}
        )
    
##############################
## Get All Students JWT
##############################

# @router.get("/all", tags=["students"])
# async def get_all_students(
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != RoleEnum.instructor:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail={"status": "error", "message": "Only instructors can access students list", "data": {}}
#         )

#     stmt = select(User).where(User.role == RoleEnum.student)
#     result = await db.execute(stmt)
#     students = result.scalars().all()

#     return {
#         "detail": {
#             "status": "success",
#             "data": [
#                 {"id": s.id, "name": s.name, "email": s.email}
#                 for s in students
#             ]
#         }
#     }

@router.get("/all", tags=["students"])
async def get_all_students(
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Fetch all students
    result = await db.execute(
        select(User).where(User.role == RoleEnum.student)
    )
    students = result.scalars().all()

    if not students:
        return {
            "detail": {
                "status": "success",
                "data": []
            }
        }

    student_ids = [s.id for s in students]

    # 2️⃣ Fetch all purchased courses
    purchased_result = await db.execute(
        select(PurchasedCourse.student_id, PurchasedCourse.course_id)
        .where(PurchasedCourse.student_id.in_(student_ids))
    )

    purchased_map = {}
    for student_id, course_id in purchased_result.all():
        purchased_map.setdefault(student_id, []).append(course_id)

    # 3️⃣ Fetch all assigned courses
    assigned_result = await db.execute(
        select(AssignedCourse.student_id, AssignedCourse.course_id)
        .where(AssignedCourse.student_id.in_(student_ids))
    )

    assigned_map = {}
    for student_id, course_id in assigned_result.all():
        assigned_map.setdefault(student_id, []).append(course_id)

    # 4️⃣ Build response
    data = []
    for s in students:
        purchased_ids = purchased_map.get(s.id, [])
        assigned_ids = assigned_map.get(s.id, [])

        combined_courses = [
            {"course_id": cid}
            for cid in set(purchased_ids + assigned_ids)
        ]

        data.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "phone_no": s.phone_no,
            "assigned_courses": combined_courses,
            "purchased_courses": [
                {"course_id": cid} for cid in purchased_ids
            ]
        })

    return {
        "detail": {
            "status": "success",
            "data": data
        }
    }



#####################################################################################################################################

##############################
## Get Id based Students JWT
##############################

# @router.get("/{student_id}", tags=["students"])
# async def get_student_by_id(
#     student_id: int,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user)
# ):
#     # Allow if instructor OR student is accessing their own profile
#     if current_user.role != RoleEnum.instructor and current_user.id != student_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail={"status": "error", "message": "Only instructors or the student themselves can view this profile", "data": {}}
#         )

#     stmt = select(User).where(User.id == student_id, User.role == RoleEnum.student)
#     result = await db.execute(stmt)
#     student = result.scalar_one_or_none()

#     if not student:
#         raise HTTPException(
#             status_code=404,
#             detail={
#                 "status": "error",
#                 "message": f"Student with ID {student_id} not found",
#                 "data": {}
#             }
#         )

#     return {
#         "detail": {
#             "status": "success",
#             "message": "Student fetched successfully",
#             "data": {
#                 "id": student.id,
#                 "name": student.name,
#                 "email": student.email,
#                 "phone_no": student.phone_no,
#                 "created_at": student.created_at.isoformat()
#             }
#         }
#     }

##########################################################################################################
## GET Student by ID + Purchased Courses Without JWT
##########################################################################################################

# @router.get("/{student_id}", tags=["students"])
# async def get_student_by_id(
#     student_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     # Fetch student
#     stmt = select(User).where(
#         User.id == student_id,
#         User.role == RoleEnum.student
#     )
#     result = await db.execute(stmt)
#     student = result.scalar_one_or_none()

#     if not student:
#         return {
#             "status": "success",
#             "message": f"Student with ID {student_id} not found",
#             "data": {}
#         }

#     # Fetch purchased courses (JOIN purchased_courses + courses)
#     course_stmt = (
#         select(Course)
#         .join(PurchasedCourse, PurchasedCourse.course_id == Course.id)
#         .where(PurchasedCourse.student_id == student_id)
#     )
#     course_result = await db.execute(course_stmt)
#     courses = course_result.scalars().all()

#     # Build response
#     return {
#         "status": "success",
#         "message": "Student fetched successfully",
#         "data": {
#             "id": student.id,
#             "name": student.name,
#             "email": student.email,
#             "phone_no": student.phone_no,
#             "registered_on": student.created_at,

#             # Assigned Course (Purchased)
#             "assigned_courses": [
#                 {
#                     "course_id": c.id,
#                     "course_name": c.title
#                 }
#                 for c in courses
#             ] if courses else "N/A"
#         }
#     }

@router.get("/{student_id}", tags=["students"])
async def get_student_by_id(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    # 1️⃣ Fetch student
    stmt = select(User).where(
        User.id == student_id,
        User.role == RoleEnum.student
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if not student:
        return {
            "status": "success",
            "message": f"Student with ID {student_id} not found",
            "data": {}
        }

    # 2️⃣ Fetch purchased courses
    purchased_stmt = (
        select(Course)
        .join(PurchasedCourse, PurchasedCourse.course_id == Course.id)
        .where(PurchasedCourse.student_id == student_id)
    )
    purchased_result = await db.execute(purchased_stmt)
    purchased_courses = purchased_result.scalars().all()

    # 3️⃣ Fetch assigned courses
    assigned_stmt = (
        select(Course)
        .join(AssignedCourse, AssignedCourse.course_id == Course.id)
        .where(AssignedCourse.student_id == student_id)
    )
    assigned_result = await db.execute(assigned_stmt)
    assigned_courses = assigned_result.scalars().all()

    # 4️⃣ Merge & remove duplicates
    courses_map = {}

    for c in purchased_courses:
        courses_map[c.id] = {
            "course_id": c.id,
            "course_name": c.title,
            "access_type": "purchased"
        }

    for c in assigned_courses:
        if c.id not in courses_map:
            courses_map[c.id] = {
                "course_id": c.id,
                "course_name": c.title,
                "access_type": "assigned"
            }

    assigned_courses_response = list(courses_map.values())

    # 5️⃣ Final response
    return {
        "status": "success",
        "message": "Student fetched successfully",
        "data": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "phone_no": student.phone_no,
            "registered_on": student.created_at,
            "assigned_courses": assigned_courses_response if assigned_courses_response else "N/A"
        }
    }


##############################
## Put Method
# OWNER AKHILESH
##############################

class StudentUpdate(BaseModel):
    Name: str
    PhoneNo: str = Field(..., alias="Phone No")

    @field_validator("PhoneNo")
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits long.")
        return v


@router.put("/{student_id}", tags=["students"])
async def update_student(
    student_id: int,
    update_data: StudentUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Fetch the student record
        stmt = select(User).where(User.id == student_id)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Student not found",
                    "data": {}
                }
            )

        # Update only Name and Phone Number
        student.name = update_data.Name
        student.phone_no = update_data.PhoneNo

        db.add(student)
        await db.commit()
        await db.refresh(student)

        return {
            "detail": {
                "status": "success",
                "message": "Student name and phone number updated successfully",
                "data": {
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                    "phone_no": student.phone_no,
                }
            }
        }

    except IntegrityError as e:
        await db.rollback()
        if "users_phone_no_key" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": "Phone number already exists",
                    "data": {}
                }
            )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to update student: {str(e)}",
                "data": {}
            }
        )

#########################################################
    
##############################
## Student login
## OWNER ANISHA
##############################

@router.post("/login", tags=["students"])
async def student_login(request: LoginRequestDetails, db: Session = Depends(get_session)):
    try:
        student = await get_user_by_email(request.Email, db)

        if student is None or student.role != RoleEnum.student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Enter valid  Email.", "data": {}}
            )

        if not verify_password(request.Password, student.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "message": "Incorrect password.", "data": {}}
            )

        # Create JWT token
        # access_token = create_access_token(
        #     data={"sub": student.id},
        #     expires_delta=timedelta(minutes=30)
        # )
        # access_token = create_access_token(
        #     student.email,  # Pass the email directly (as a string)
        #     expires_delta=timedelta(minutes=30)
        # )
        access_token = create_access_token(
        user_id=student.id,
        expires_delta=timedelta(minutes=30)
        )


        return {
            "detail": {
                "status": "success",
                "message": "Logged in successfully",
                "data": {
                    "id": student.id,
                    "studentName": student.name,
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            }
        }
    

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to process login request: {str(e)}",
                "data": {}
            }
        )

#####################################################################################################################
## OWNER AKHILESH this code using http cookie
#####################################################################################################################



# @router.post("/logout", tags=["students"])
# async def logout(response: Response):
#     response.delete_cookie("access_token")
#     return {
#         "status": "success",
#         "message": "Logged out successfully"
#     }


