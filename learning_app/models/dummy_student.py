from pydantic import BaseModel
from typing import List
from .course import Course

class DummyStudent(BaseModel):
    student_id: int
    name: str
    email: str
    purchased_courses: List[Course]

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }
