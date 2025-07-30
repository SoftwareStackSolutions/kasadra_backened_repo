from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from learning_app.database.db import get_session
from models.student import Student, TokenTable
from learning_app.common import get_student_by_email

router = APIRouter()
class StudentCreate(BaseModel):
    name: str
    email: str
    password: str

class LoginRequestDetails(BaseModel):
    email: str
    password: str    

class StudentUpdate(BaseModel):
    name: str   
    email: str
    password: str 

@router.post("/create", tags=["students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_session)):
    new_student = None

    try:
        #employye_name_exists = employee_crud.get_employee_by_email(session, email=employee.email)
        student_exists = await get_student_by_email(student, db)
        if student_exists:
            response = {"status":"error", "message": "Email already registered", "data": {}}
            raise HTTPException (status_code=status.HTTP_409_CONFLICT, detail=response)
        new_student = Student(name=student.name,
                        email=student.email,
                        password=student.password)

        db.add(new_student)
        await db.commit()
        await db.refresh(new_student)
        response = {"status":"success", "message": "Student created successfully", "data": {"studentID": new_student.student_id}}
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
        
        if request.password == student.password:
            response = {"status":"success", "message": "Loggged in successfully", "data": {"userId": student.student_id, "studentName": student.name}}
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