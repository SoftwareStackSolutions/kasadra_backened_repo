from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_PASSWORD_BYTES = 72

def hash_password(password: str) -> str:
    # Convert password to bytes
    password_bytes = password.encode("utf-8")
    
    # Truncate safely to 72 bytes
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        password_bytes = password_bytes[:MAX_BCRYPT_PASSWORD_BYTES]
    
    # Decode back to string safely
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        password_bytes = password_bytes[:MAX_BCRYPT_PASSWORD_BYTES]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(truncated_password, hashed_password)
