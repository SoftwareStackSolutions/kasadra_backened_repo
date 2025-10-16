from pydantic import BaseModel

class CartBase(BaseModel):
    course_id: int
    student_id: int

class CartResponse(BaseModel):
    id: int
    student_id: int
    course_id: int

    class Config:
        orm_mode = True
