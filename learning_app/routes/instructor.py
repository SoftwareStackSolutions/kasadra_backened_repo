from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from sqlalchemy import func
import re
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from database.db import get_session
from models.instructor import Instructor, TokenTable
from common import get_instructor_by_email

router = APIRouter()
class InstructorCreate(BaseModel):
    Name: str
    Email: EmailStr
    PhoneNo: str = Field(..., alias="Phone No")
    Password: str
    Confirmpassword: str = Field(..., alias="Confirm Password")
    
    @field_validator("PhoneNo")
    @classmethod
    def validate_phone_number(cls, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be a 10-digit number")
        return value
    
    @model_validator(mode="after")
    def check_password_match(self) -> "InstructorCreate":
        if self.Password != self.Confirmpassword:
            raise ValueError("Password incorrect")
        return self

    model_config = {
        "populate_by_name": True,
        "alias_generator": None,
        "json_encoders": {}
    }

class LoginRequestDetails(BaseModel):
    Email: EmailStr
    Password: str    

@router.post("/create", tags=["instructors"])
async def create_instructor(instructor: InstructorCreate, db: Session = Depends(get_session)):
    new_instructor = None

    try:
        #employye_name_exists = employee_crud.get_employee_by_email(session, email=employee.email)
        instructor_exists = await get_instructor_by_email(instructor, db)
        if instructor_exists:
            response = {"status":"error", "message": "Email already registered", "data": {}}
            raise HTTPException (status_code=status.HTTP_409_CONFLICT, detail=response)
        new_instructor = Instructor(name=instructor.Name,
                        email=instructor.Email,
                        phone_no=instructor.PhoneNo,
                        password=instructor.Password,
                        confirm_password=instructor.Confirmpassword
                        )

        db.add(new_instructor)
        await db.commit()
        await db.refresh(new_instructor)
        response = {"status":"success", "message": "Instructor created successfully", "data": {"id": new_instructor.id}}
        return {"detail": response}
    
    except HTTPException as e:
        # Re-raise the original HTTPException
        raise e        
    
    except Exception as e:
        # logger.debug(f"Error in create_user endpoint: {str(e)}")
        response = {"status": "error", "message": f"Failed to create instructor: {str(e)}", "data": {"id": new_instructor }}
        raise HTTPException(status_code=500, detail=response)


@router.post("/login", tags=["instructors"])
async def instructor_login(request: LoginRequestDetails, db : Session = Depends(get_session)):

    try:
        instructor = await get_instructor_by_email(request, db)
        if instructor is None:
            # import pdb;pdb.set_trace()
        
            # logger.info("Get EmployeeByEmail response: Incorrect email")
            response = {"status":"error", "message": "Incorrect email.", "data": {}}
            raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, detail=response)
        
        if request.Password == instructor.password:
            response = {"status":"success", "message": "Loggged in successfully", "data": {"id": instructor.id, "instructorName": instructor.name}}
            return {"detail": response}
        else:
            # logger.info("Post employee_login response: Incorrect password.")
            response = {"status":"error", "message": "Incorrect password.", "data": {}}
            raise HTTPException (status_code=status.HTTP_401_UNAUTHORIZED, detail=response)
        
    except HTTPException as e:
         # Re-raise the original HTTPException
        raise e     
    
    except Exception as e:
        # logger.debug(f"Error in employee_login endpoint for employeename:{str(e)}")
        response = {"status": "error", "message": f"Failed to process login request:: {str(e)}", "data": {}}
        raise HTTPException(status_code=500, detail=response)   