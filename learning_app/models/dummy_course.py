from pydantic import BaseModel

class DummyCourse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True  # instead of orm_mode in Pydantic v2
