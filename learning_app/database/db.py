# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.asyncio import AsyncSession

# from database.dbconfig import engine

# async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# async def get_session() -> AsyncSession:
#     async with async_session() as session:
#         yield session

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
#############################################################################################

### Owner= Akhilesh ML

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models import user  # all models must be imported
from database.dbconfig import SQLALCHEMY_DATABASE_URL

# Create engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Create session
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Session dependency for FastAPI
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# Function to create tables on app startup
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

