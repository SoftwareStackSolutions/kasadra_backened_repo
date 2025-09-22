from pydantic import BaseModel
from typing import Optional

class CourseCreate(BaseModel):
    title: str
    description: str
    duration: str
    thumbnail: Optional[str] = None
    # instructor_id: Optional[int] = None

class LessonCreate(BaseModel):
    title: str
    description: str | None = None
    course_id: Optional[int] = None
    file_content: str | None = None
    
class ConceptCreate(BaseModel):
    lesson_id: int
    lesson_title: str
    concept_title: str
    description: Optional[str] = None
    file_content: Optional[str] = None