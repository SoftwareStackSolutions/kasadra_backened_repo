##########################
from passlib.hash import bcrypt
 
def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password cannot exceed 72 characters")
    return bcrypt.hash(password)

##############################


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_PASSWORD_BYTES = 72

def hash_password(password: str) -> str:
    # Truncate password to 72 bytes for bcrypt
    password_bytes = password.encode("utf-8")[:MAX_BCRYPT_PASSWORD_BYTES]
    truncated_password = password_bytes.decode("utf-8", "ignore")
    return pwd_context.hash(truncated_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate input for verification too
    password_bytes = plain_password.encode("utf-8")[:MAX_BCRYPT_PASSWORD_BYTES]
    truncated_password = password_bytes.decode("utf-8", "ignore")
    return pwd_context.verify(truncated_password, hashed_password)
