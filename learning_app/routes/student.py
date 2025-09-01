from fastapi import APIRouter, Depends, HTTPException, status
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

from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation 


router = APIRouter()

#  Pydantic Schemas 
class StudentCreate(BaseModel):
    Name: str
    Email: EmailStr
    PhoneNo: str = Field(..., alias="Phone No")
    Password: str
    Confirmpassword: str = Field(..., alias="Confirm Password")

    @field_validator("PhoneNo")
    @classmethod
    def validate_phone(cls, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be 10 digits")
        return value

    @model_validator(mode="after")
    def check_password_match(self):
        if self.Password != self.Confirmpassword:
            raise ValueError("Passwords do not match")
        return self

    model_config = {
        "populate_by_name": True
    }

class LoginRequestDetails(BaseModel):
    Email: EmailStr
    Password: str

##############################
## Create Students 
##############################

@router.post("/create", tags=["students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_session)):
    try:
        student_exists = await get_user_by_email(student.Email, db)
        if student_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": "Email already registered",
                    "data": {}
                }
            )

        new_student = User(
            name=student.Name,
            email=student.Email,
            phone_no=student.PhoneNo,
            password=hash_password(student.Password),
            confirm_password=hash_password(student.Confirmpassword),
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
######################################################
## owner AK

    except IntegrityError as e:
        await db.rollback()
        # Check if it's phone_no duplicate
        if "users_phone_no_key" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": "Phone number already exists",
                    "data": {}
                }
            )

######################################################


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to create student: {str(e)}",
                "data": {}
            }
        )

##############################
## Get All Students 
##############################

@router.get("/all", tags=["students"])
async def get_all_students(db: Session = Depends(get_session)):
    try:
        stmt = select(User).where(User.role == RoleEnum.student)
        result = await db.execute(stmt)
        students = result.scalars().all()

        return {
            "detail": {
                "status": "success",
                "message": "Students fetched successfully",
                "data": [ 
                    {
                        "id": i.id,
                        "name": i.name,
                        "email": i.email,
                        "phone_no": i.phone_no
                    } for i in students
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to fetch students: {str(e)}",
                "data": {}
            }
        )
    
##############################
## Get Id based Students 
##############################
@router.get("/{student_id}", tags=["students"])
async def get_instructor_by_id(student_id: int, db: Session = Depends(get_session)):
    try:
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
                    "phone_no": student.phone_no
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to fetch instructor: {str(e)}",
                "data": {}
            }
        )
    
##########################################################################################################

#### Put Method

#  Pydantic Schemas 
class StudentUpdate(BaseModel):   
    Name: str
    Email: EmailStr
    PhoneNo: str = Field(..., alias="Phone No")

    @field_validator("PhoneNo")
    def validate_phone(cls, v):
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits long.")
        return v

@router.put("/{student_id}", tags=["students"])
async def update_student(
    student_id: int,
    update_data: StudentUpdate,
    db: AsyncSession = Depends(get_session)
):
    try:
        # Fetch student
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

        # Update fields only if provided
        if update_data.Name:
            student.name = update_data.Name
        if update_data.Email:
            student.email = update_data.Email
        if update_data.PhoneNo:
            student.phone_no = update_data.PhoneNo

        db.add(student)
        await db.commit()
        await db.refresh(student)

        return {
            "detail": {
                "status": "success",
                "message": "Student updated successfully",
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
        if "users_email_key" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": "Email already exists",
                    "data": {}
                }
            )
        elif "users_phone_no_key" in str(e.orig):
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
##############################

@router.post("/login", tags=["students"])
async def student_login(request: LoginRequestDetails, db: Session = Depends(get_session)):
    try:
        student = await get_user_by_email(request.Email, db)

        if student is None or student.role != RoleEnum.student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Incorrect email.", "data": {}}
            )

        if not verify_password(request.Password, student.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "message": "Incorrect password.", "data": {}}
            )

        # Create JWT token
        access_token = create_access_token(
            data={"sub": student.id},
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
