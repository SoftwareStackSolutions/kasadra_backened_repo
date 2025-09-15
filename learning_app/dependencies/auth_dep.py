from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from database.db import get_session
from utils.auth import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> User:
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "Invalid or expired token", "data": {}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload.get("sub"))  # Convert safely to int
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "Invalid token payload", "data": {}}
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": "User not found", "data": {}}
        )

    return user




# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.ext.asyncio import AsyncSession
# from utils.auth import verify_access_token
# from learning_app.database.db import get_session
# from learning_app.models.user import User
# from sqlalchemy.future import select


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)):
#     payload = verify_access_token(token)
#     if payload is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail={"status": "error", "message": "Invalid or expired token", "data": {}},
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     stmt = select(User).where(User.id == payload.get("sub"))
#     result = await db.execute(stmt)
#     user = result.scalar_one_or_none()
    
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={"status": "error", "message": "User not found", "data": {}}
#         )
#     return user

