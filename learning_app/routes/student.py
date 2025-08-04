from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from sqlalchemy import func
import re
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from database.db import get_session
from models.student import Student, TokenTable
from common import get_student_by_email

router = APIRouter()
class StudentCreate(BaseModel):
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
    def check_password_match(self) -> "StudentCreate":
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

@router.post("/create", tags=["students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_session)):
    new_student = None

    try:
        #employye_name_exists = employee_crud.get_employee_by_email(session, email=employee.email)
        student_exists = await get_student_by_email(student, db)
        if student_exists:
            response = {"status":"error", "message": "Email already registered", "data": {}}
            raise HTTPException (status_code=status.HTTP_409_CONFLICT, detail=response)
        new_student = Student(name=student.Name,
                        email=student.Email,
                        phone_no=student.PhoneNo,
                        password=student.Password,
                        confirm_password=student.Confirmpassword
                        )

        db.add(new_student)
        await db.commit()
        await db.refresh(new_student)
        response = {"status":"success", "message": "Student created successfully", "data": {"id": new_student.id}}
        return {"detail": response}
    
    except HTTPException as e:
        # Re-raise the original HTTPException
        raise e        
    
    except Exception as e:
        # logger.debug(f"Error in create_user endpoint: {str(e)}")
        response = {"status": "error", "message": f"Failed to create student: {str(e)}", "data": {"studentID": new_student }}
        raise HTTPException(status_code=500, detail=response)
    
        
@router.post("/login", tags=["students"])
async def student_login(request: LoginRequestDetails, db : Session = Depends(get_session)):

    try:
        student = await get_student_by_email(request, db)
        if student is None:
            # import pdb;pdb.set_trace()
        
            # logger.info("Get EmployeeByEmail response: Incorrect email")
            response = {"status":"error", "message": "Incorrect email.", "data": {}}
            raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, detail=response)
        
        if request.Password == student.password:
            response = {"status":"success", "message": "Loggged in successfully", "data": {"id": student.id, "studentName": student.name}}
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