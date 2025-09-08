from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

# from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:admin12@localhost/kasadara"

# engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

#####################################################################
## Owner= Akhilesh ML


# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://admin:admin12@34.57.39.15:5432/kasadara"
# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://admin:admin12@postgres-service.kasadara.svc.cluster.local:5432/kasadara"

import os
from dotenv import load_dotenv

load_dotenv()  # Loads .env if present

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT") or 5432
DB_NAME = os.getenv("POSTGRES_DB")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
#####################################################################

