from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
 
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:admin12@localhost:5432/kasadara"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)