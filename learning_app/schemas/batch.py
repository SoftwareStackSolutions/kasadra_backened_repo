from pydantic import BaseModel
from typing import List

class AssignStudentsRequest(BaseModel):
    batch_id: int
    student_ids: List[int]

# from pydantic import BaseModel

# class BatchCreate(BaseModel):
#     course_id: int
#     batch_name: str
#     instructor_id: int

#     class Config:
#         from_attributes = True
