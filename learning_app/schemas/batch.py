from pydantic import BaseModel
from typing import List

class AssignStudentsRequest(BaseModel):
    batch_id: int
    student_ids: List[int]
