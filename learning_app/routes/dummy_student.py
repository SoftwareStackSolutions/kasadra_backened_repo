from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from routes.dummy_course import COURSE_CATALOG

router = APIRouter()

class DummyStudent(BaseModel):
    student_id: int
    name: str
    email: str
    purchased_courses: List[dict]

# Dummy student database
STUDENTS_DB = [
    {
        "student_id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "purchased_courses": [COURSE_CATALOG[0], COURSE_CATALOG[2]],
    },
    {
        "student_id": 2,
        "name": "Bob",
        "email": "bob@example.com",
        "purchased_courses": [COURSE_CATALOG[1], COURSE_CATALOG[3]],
    },
    {
        "student_id": 3,
        "name": "Domi",
        "email": "domi@example.com",
        "purchased_courses": [COURSE_CATALOG[4]],
    },
]

@router.get("/dummy/students", response_model=List[DummyStudent])
async def get_dummy_students():
    return STUDENTS_DB
