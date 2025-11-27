from pydantic import BaseModel

class AssignStudentRequest(BaseModel):
    student_id: int
    batch_id: int
