from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
 
# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:admin12@localhost:5432/kasadara"

#####################################################################
## Owner= Akhilesh ML


SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://admin:admin12@34.57.39.15:5432/kasadara"

#####################################################################


engine = create_async_engine(SQLALCHEMY_DATABASE_URL)