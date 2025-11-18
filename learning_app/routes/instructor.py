from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from sqlalchemy.orm import Session
from utils.passwd import hash_password, verify_password
import re
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models.user import User, RoleEnum
from database.db import get_session
from common import get_user_by_email
from utils.auth import create_access_token
from datetime import timedelta
from dependencies.auth_dep import get_current_user


router = APIRouter()

class InstructorCreate(BaseModel):
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
### Create instructors
##############################

@router.post("/create", tags=["instructors"])
async def create_instructor(instructor: InstructorCreate, db: Session = Depends(get_session)):
    try:
        instructor_exists = await get_user_by_email(instructor.Email, db)
        if instructor_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": "Email already registered",
                    "data": {}
                }
            )

        new_instructor = User(
            name=instructor.Name,
            email=instructor.Email,
            phone_no=instructor.PhoneNo,
            password=hash_password(instructor.Password),
            role=RoleEnum.instructor
        )

        db.add(new_instructor)
        await db.commit()
        await db.refresh(new_instructor)

        return {
            "detail": {
                "status": "success",
                "message": "Instructor created successfully",
                "data": {"id": new_instructor.id}
            }
        }

    except HTTPException as e:
        raise e
    
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to create instructor: {str(e)}",
                "data": {}
            }
        )

##############################
## Get all instructors details
##############################

@router.get("/all", tags=["instructors"])
async def get_all_instructors(db: Session = Depends(get_session)):
    try:
        stmt = select(User).where(User.role == RoleEnum.instructor)
        result = await db.execute(stmt)
        instructors = result.scalars().all()

        return {
            "detail": {
                "status": "success",
                "message": "Instructors fetched successfully",
                "data": [ 
                    {
                        "id": i.id,
                        "name": i.name,
                        "email": i.email,
                        "phone_no": i.phone_no
                    } for i in instructors
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to fetch instructors: {str(e)}",
                "data": {}
            }
        )

##############################
### Get instuctor by id
##############################    

@router.get("/{instructor_id}", tags=["instructors"])
async def get_instructor_by_id(
    instructor_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)  # 👈 JWT protection here
):
    try:
        stmt = select(User).where(User.id == instructor_id, User.role == RoleEnum.instructor)
        result = await db.execute(stmt)
        instructor = result.scalar_one_or_none()

        if not instructor:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Instructor with ID {instructor_id} not found",
                    "data": {}
                }
            )

        return {
            "detail": {
                "status": "success",
                "message": "Instructor fetched successfully",
                "data": {
                    "id": instructor.id,
                    "name": instructor.name,
                    "email": instructor.email,
                    "phone_no": instructor.phone_no
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

##############################
## Instructors login
##############################

@router.post("/login", tags=["instructors"])
async def instructor_login(
    request: LoginRequestDetails,
    db: Session = Depends(get_session)
):
    try:
        # Fetch user by email
        instructor = await get_user_by_email(request.Email, db)

        # Validate existence and role
        if instructor is None or instructor.role != RoleEnum.instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Incorrect email or role", "data": {}}
            )

        # Validate password
        if not verify_password(request.Password, instructor.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "message": "Incorrect password", "data": {}}
            )

        # Create JWT token (Correct usage)
        access_token = create_access_token(
            user_id=instructor.id,
            expires_delta=timedelta(minutes=30)
        )

        return {
            "detail": {
                "status": "success",
                "message": "Logged in successfully",
                "data": {
                    "id": instructor.id,
                    "instructorName": instructor.name,
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
