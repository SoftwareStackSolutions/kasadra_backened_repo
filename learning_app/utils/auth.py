# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from models.user import User
from database.db import get_session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional



# ⚡ Config (Replace SECRET_KEY with your real secret key)
# JWT Settings
SECRET_KEY = "supersecretkeychangeit"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = {"sub": str(user_id)}  # Store user ID as string
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": str(user_id)}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            return None
        return payload  # Contains {"sub": "<user_id>", "exp": "..."}
    except JWTError:
        return None


# -----------------------------
# Dependency for FastAPI
# -----------------------------
# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_session)
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     payload = verify_access_token(token)  # Use directly, no import needed
#     if payload is None:
#         raise credentials_exception

#     email: str = payload.get("sub")
#     if email is None:
#         raise credentials_exception

#     result = await db.execute(select(User).where(User.email == email))
#     user = result.scalars().first()
#     if user is None:
#         raise credentials_exception

#     return user








#####################################
## OWNER ANISHA 
#####################################

# from datetime import datetime, timedelta
# from typing import Optional
# from jose import JWTError, jwt

# # Secret key for JWT signing (keep it safe!)
# SECRET_KEY = "supersecretkeychangeit"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def verify_access_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload  # Returns dict with 'sub' (user email/ID)
#     except JWTError:
#         return None
