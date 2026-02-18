import os
import sys
from dotenv import load_dotenv

# ----------------------------------
# Load Correct ENV File
# ----------------------------------
ENV = os.getenv("ENV", "development")

if ENV == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.development")

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

# ----------------------------------
# Fix path
# ----------------------------------
root_dir = os.path.dirname(__file__)
sys.path.append(root_dir)

# --------------------------------------------------
# Fix path
# --------------------------------------------------
root_dir = os.path.dirname(__file__)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "database"))
sys.path.append(os.path.join(root_dir, "models"))
sys.path.append(os.path.join(root_dir, "routes"))
sys.path.append(os.path.join(root_dir, "data"))

# --------------------------------------------------
# DB
# --------------------------------------------------
from database.db import Base, init_db
from database.dbconfig import engine
from seed.subscription_seed import seed_subscription_plans

# --------------------------------------------------
# Routers
# --------------------------------------------------
from routes.tenent import subscription_plan
from routes.tenent import org_signup
from routes.tenent import gmail_otp
from routes.tenent import auth

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
from routes import lesson_activate
from routes.ai import router as ai_router
from routes.holidaydir import holiday

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(
    title="Learning_App",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ----------------------------------
# CORS (VERY IMPORTANT)
# ----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://digidense.com",
        "https://learn.digidense.com",
    ],
    allow_credentials=True,   # MUST be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------------------
# Include Routers
# --------------------------------------------------
app.include_router(subscription_plan.router, prefix="/api/tenant")
app.include_router(org_signup.router, prefix="/api/tenant")
app.include_router(gmail_otp.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

app.include_router(student.router, prefix="/api/student")
app.include_router(instructor.router, prefix="/api/instructor")
app.include_router(course.router, prefix="/api/courses")
app.include_router(lessons.router, prefix="/api/lessons")
app.include_router(scheduleclass.router, prefix="/api/scheduleclass")
app.include_router(batch.router, prefix="/api/batches")
app.include_router(cart.router, prefix="/api/cart")
app.include_router(purchased_course.router, prefix="/api/buy")

app.include_router(contents.pdf_router, prefix="/api/contents")
app.include_router(contents.weblink_router, prefix="/api/contents")
app.include_router(contents.quiz_router, prefix="/api/contents")
app.include_router(contents.lab_router, prefix="/api/contents")

app.include_router(meeting_link.router, prefix="/api")
app.include_router(lesson_activate.router, prefix="/api/activate")

app.include_router(ai_router)
app.include_router(holiday.router, prefix="/api")

# --------------------------------------------------
# Startup Event (ONLY ONE)
# --------------------------------------------------
@app.on_event("startup")
async def startup():
    await init_db()
    await seed_subscription_plans()

# --------------------------------------------------
# Root & Health
# --------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# --------------------------------------------------
# Global Exception Handler
# --------------------------------------------------
@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred"},
    )

# --------------------------------------------------
# Validation Handler
# --------------------------------------------------
@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request: Request, exc: RequestValidationError):

    for err in exc.errors():
        if err["type"] == "json_invalid":
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Your JSON contains invalid or unsupported characters."
                }
            )

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid input data",
            "detail": exc.errors()
        }
    )

# --------------------------------------------------
# Run Server
# --------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
