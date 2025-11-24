import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from database.db import Base
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from json import JSONDecodeError

root_dir = os.path.dirname(__file__)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "database"))
sys.path.append(os.path.join(root_dir, "models"))
sys.path.append(os.path.join(root_dir, "routes"))
sys.path.append(os.path.join(root_dir, "data"))

from database.dbconfig import engine

from routes import student
from routes import instructor
from routes import course
from routes import lessons
from routes import scheduleclass
from routes import batch
from routes import contents
from routes import cart
from routes import purchased_course
from routes import meeting_link
from routes import contents, lesson_activate
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

app = FastAPI(
    title="Learning_App",
    description="agent backend",
    version="1.0.0",
    openapi_version="3.0.3",
    docs_url="/api/docs",           # Swagger UI
    redoc_url="/api/redoc",         # ReDoc
    openapi_url="/api/openapi.json" # OpenAPI schema
)

# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(student.router, prefix="/api/student")
app.include_router(instructor.router, prefix="/api/instructor")
app.include_router(course.router, prefix="/api/courses")
app.include_router(lessons.router, prefix="/api/lessons")
app.include_router(scheduleclass.router, prefix="/api/scheduleclass")
app.include_router(batch.router, prefix="/api/batches")
app.include_router(cart.router,prefix="/api/cart")
app.include_router(purchased_course.router,prefix="/api/buy")
app.include_router(contents.pdf_router,prefix="/api/contents")
app.include_router(contents.weblink_router,prefix="/api/contents")
app.include_router(contents.quiz_router,prefix="/api/contents")
app.include_router(contents.lab_router,prefix="/api/contents")
app.include_router(meeting_link.router,prefix="/api")
app.include_router(lesson_activate.router,prefix="/api/activate")

origins = [
    "http://localhost:5173",   # React dev server
    "http://127.0.0.1:5173",   
    "http://127.0.0.1:8000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:8000", 
    "http://127.0.0.1:8000/docs",
    "http://127.0.0.1:8000/api/docs",
    "http://www.softwarestack.xyz/api/",
    "http://www.softwarestack.xyz",
    "http://www.softwarestack.xyz/api/docs"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # Create the database tables.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
@app.exception_handler(Exception)
async def universal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred"},
    )
    

#####################################################################

## Owner= Akhilesh ML

from database.db import init_db  # NOT from models.base

## health check
@app.get("/api")
async def health_check():
    return {"status": "ok"}


## DB setup
@app.on_event("startup")
async def startup_event():
    await init_db()


@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request: Request, exc: RequestValidationError):

    # Detect JSON decode error
    for err in exc.errors():
        if err["type"] == "json_invalid":
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Your JSON contains invalid or unsupported characters. Please clean the text.",
                }
            )

    # Other validation errors
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid input data",
            "detail": exc.errors()
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

