# core/security.py

from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os


load_dotenv()  

SECRET_KEY = os.getenv("SECRET_KEY")
print("SECRET_KEY:", SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

security = HTTPBearer(auto_error=False)


# -------------------------
# Create Token
# -------------------------
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# Decode Token
# -------------------------
def decode_access_token(token: str):
    try:
        print("SECRET_KEY used:", SECRET_KEY)
        print("TOKEN received:", token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("DECODED:", payload)
        return payload
    except JWTError as e:
        print("JWT ERROR:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# -------------------------
# Dependency: Get Current Org
# -------------------------
def get_current_org(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Handle missing Authorization header
    if credentials is None:
        print("No Authorization header received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = credentials.credentials

    print("Authorization Header:", credentials)
    print("Bearer Token:", token)

    payload = decode_access_token(token)
    print("Decoded Payload:", payload)

    return payload
