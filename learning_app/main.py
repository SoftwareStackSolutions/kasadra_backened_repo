
import os
import sys
import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

root_dir = os.path.dirname(__file__)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "database"))
sys.path.append(os.path.join(root_dir, "models"))
sys.path.append(os.path.join(root_dir, "routes"))
sys.path.append(os.path.join(root_dir, "data"))

from database.dbconfig import engine
from models.base import Base

from routes import student
from routes import instructor
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

app = FastAPI(
    title="agent app",
    description="agent backend",
    version="1.0.0",
    openapi_version="3.0.3"
)
app.include_router(student.router, prefix="/api/student")
app.include_router(instructor.router, prefix="/api/instructor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
