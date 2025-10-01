from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class DummyCourse(BaseModel):
    id: int
    name: str
    description: str


# Dummy course catalog (5 courses)
COURSE_CATALOG = [
    {"id": 1, "name": "Python", "description": "Learn Python fundamentals"},
    {"id": 2, "name": "FastAPI", "description": "Build APIs quickly"},
    {"id": 3, "name": "Docker", "description": "Containerize applications"},
    {"id": 4, "name": "Terraform on AWS", "description": "Infrastructure as Code"},
    {"id": 5, "name": "DevOps", "description": "Build CI/CD pipelines"},
]

@router.get("/dummy/courses", response_model=List[DummyCourse])
async def get_dummy_courses():
    return COURSE_CATALOG
