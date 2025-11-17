from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
from datetime import date, time, datetime


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

############################################
## ScheduleCreate
############################################
class ScheduleCreate(BaseModel):
    course_id: int
    lesson_id: int
    instructor_id: int
    session_date: date
    session_time: time

class ScheduleResponse(BaseModel):
    id: int
    course_id: int
    lesson_id: int
    instructor_id: int
    session_date: date
    session_time: time

    class Config:
        orm_mode = True


#####################
## Batch create
#####################

class BatchCreate(BaseModel):
    course_id: int
    batch_name: str
    num_students: int
    instructor_id: int
    timing: Optional[str] = None
    start_date: date
    end_date: date

#####################
## Meeting link
#####################

class MeetingCreate(BaseModel):
    instructor_id: int     # temporary until JWT added
    course_id: int
    batch_id: int
    meeting_url: HttpUrl

class MeetingResponse(BaseModel):
    id: int
    instructor_id: int
    course_id: int
    batch_id: int
    meeting_url: str

    class Config:
        orm_mode = True

#####################
## Notes
#####################

class NoteCreate(BaseModel):
    course_id: int
    lesson_id: int
    instructor_id: int
    notes: Any

class NoteResponse(BaseModel):
    id: int
    course_id: int
    lesson_id: int
    notes: Any

    class Config:
        orm_mode = True
