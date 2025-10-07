# utils/passwd.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_PASSWORD_BYTES = 72

def truncate_password(password: str) -> str:
    # Encode to bytes, truncate, then decode safely
    password_bytes = password.encode("utf-8")[:MAX_BCRYPT_PASSWORD_BYTES]
    return password_bytes.decode("utf-8", errors="ignore")

def hash_password(password: str) -> str:
    safe_password = truncate_password(password)
    return pwd_context.hash(safe_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_password = truncate_password(plain_password)
    return pwd_context.verify(safe_password, hashed_password)
