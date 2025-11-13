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

@router.get("/all", tags=["students"])
async def get_all_students(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Only instructors can access students list", "data": {}}
        )

    stmt = select(User).where(User.role == RoleEnum.student)
    result = await db.execute(stmt)
    students = result.scalars().all()

    return {
        "detail": {
            "status": "success",
            "data": [
                {"id": s.id, "name": s.name, "email": s.email}
                for s in students
            ]
        }
    }

# @router.get("/all", tags=["students"])
# async def get_all_students(db: Session = Depends(get_session)):
#     try:
#         stmt = select(User).where(User.role == RoleEnum.student)
#         result = await db.execute(stmt)
#         students = result.scalars().all()

#         return {
#             "detail": {
#                 "status": "success",
#                 "message": "Students fetched successfully",
#                 "data": [ 
#                     {
#                         "id": i.id,
#                         "name": i.name,
#                         "email": i.email,
#                         "phone_no": i.phone_no,
#                         "created_at": i.created_at.isoformat() 
#                     } for i in students
#                 ]
#             }
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "message": f"Failed to fetch students: {str(e)}",
#                 "data": {}
#             }
#         )


#####################################################################################################################################

##############################
## Get Id based Students JWT
##############################

@router.get("/{student_id}", tags=["students"])
async def get_student_by_id(
    student_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Allow if instructor OR student is accessing their own profile
    if current_user.role != RoleEnum.instructor and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Only instructors or the student themselves can view this profile", "data": {}}
        )

    stmt = select(User).where(User.id == student_id, User.role == RoleEnum.student)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": f"Student with ID {student_id} not found",
                "data": {}
            }
        )

    return {
        "detail": {
            "status": "success",
            "message": "Student fetched successfully",
            "data": {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "phone_no": student.phone_no,
                "created_at": student.created_at.isoformat()
            }
        }
    }

##########################################################################################################################
##############################
## Get Id based Students 
##############################
# @router.get("/{student_id}", tags=["students"])
# async def get_instructor_by_id(student_id: int, db: Session = Depends(get_session)):
#     try:
#         stmt = select(User).where(User.id == student_id, User.role == RoleEnum.student)
#         result = await db.execute(stmt)
#         student = result.scalar_one_or_none()

#         if not student:
#             raise HTTPException(
#                 status_code=404,
#                 detail={
#                     "status": "error",
#                     "message": f"Student with ID {student_id} not found",
#                     "data": {}
#                 }
#             )

#         return {
#             "detail": {
#                 "status": "success",
#                 "message": "Student fetched successfully",
#                 "data": {
#                     "id": student.id,
    #                 "name": student.name,
    #                 "email": student.email,
    #                 "phone_no": student.phone_no,
    #                 "created_at": student.created_at.isoformat()
    #             }
    #         }
    #     }
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail={
    #             "status": "error",
    #             "message": f"Failed to fetch instructor: {str(e)}",
    #             "data": {}
    #         }
    #     )
    
##########################################################################################################

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




# # from .schemas import StudentUpdate  

# class StudentUpdate(BaseModel):   
#     Name: str
#     Email: EmailStr
#     PhoneNo: str = Field(..., alias="Phone No")

#     @field_validator("PhoneNo")
#     def validate_phone(cls, v):
#         if v is None:
#             return v
#         if not v.isdigit():
#             raise ValueError("Phone number must contain only digits.")
#         if len(v) != 10:
#             raise ValueError("Phone number must be exactly 10 digits long.")
#         return v

# @router.put("{student_id}", tags=["students"])
# async def update_student(
#     student_id: int,
#     update_data: StudentUpdate,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user)  # ✅ JWT protection
# ):
#     try:
#         # ✅ Only allow logged-in student to update their own profile
#         if current_user.id != student_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail={
#                     "status": "error",
#                     "message": "You are not authorized to update this profile",
#                     "data": {}
#                 }
#             )

#         # Fetch student from DB
#         stmt = select(User).where(User.id == student_id)
#         result = await db.execute(stmt)
#         student = result.scalar_one_or_none()

#         if not student:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail={
#                     "status": "error",
#                     "message": "Student not found",
#                     "data": {}
#                 }
#             )

#         # Update only allowed fields
#         if update_data.Name is not None:
#             student.name = update_data.Name
#         if update_data.Email is not None:
#             student.email = update_data.Email
#         if update_data.PhoneNo is not None:
#             student.phone_no = update_data.PhoneNo

#         db.add(student)
#         await db.commit()
#         await db.refresh(student)

#         return {
#             "detail": {
#                 "status": "success",
#                 "message": "Student updated successfully",
#                 "data": {
#                     "id": student.id,
#                     "name": student.name,
#                     "email": student.email,
#                     "phone_no": student.phone_no
#                 }
#             }
#         }

#     except IntegrityError as e:
#         await db.rollback()
#         if "users_email_key" in str(e.orig):
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail={
#                     "status": "error",
#                     "message": "Email already exists",
#                     "data": {}
#                 }
#             )
#         elif "users_phone_no_key" in str(e.orig):
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail={
#                     "status": "error",
#                     "message": "Phone number already exists",
#                     "data": {}
#                 }
#             )

#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "message": f"Failed to update student: {str(e)}",
#                 "data": {}
#             }
#         )


# @router.post("/login", tags=["students"])
# async def student_login(request: LoginRequestDetails, response: Response, db: Session = Depends(get_session)):
#     try:
#         student = await get_user_by_email(request.Email, db)

#         if student is None or student.role != RoleEnum.student:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail={"status": "error", "message": "Incorrect email.", "data": {}}
#             )

#         if not verify_password(request.Password, student.password):
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail={"status": "error", "message": "Incorrect password.", "data": {}}
#             )

#         # Create JWT token
#         access_token = create_access_token(
#             data={"sub": student.id},
#             expires_delta=timedelta(minutes=30)
#         )

#         # ✅ Store token in HTTP-only cookie
#         response.set_cookie(
#             key="access_token",
#             value=access_token,
#             httponly=True,        # JS cannot access
#             secure=True,          # Only send via HTTPS
#             samesite="lax",       # Prevent CSRF (use "strict" or "none" depending on frontend)
#             max_age=1800          # 30 minutes
#         )

#         return {
#             "detail": {
#                 "status": "success",
#                 "message": "Logged in successfully",
#                 "data": {
#                     "id": student.id,
#                     "studentName": student.name
#                 }
#             }
#         }

#     except HTTPException as e:
#         raise e

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "message": f"Failed to process login request: {str(e)}",
#                 "data": {}
#             }
#         )



# @router.post("/logout", tags=["students"])
# async def logout(response: Response):
#     response.delete_cookie("access_token")
#     return {
#         "status": "success",
#         "message": "Logged out successfully"
#     }


