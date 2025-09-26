from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# from passlib.context import CryptContext 

# pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# def hash_password(password: str) -> str:
#     """Hash the given password securely."""
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify that a plain password matches the stored hash."""
#     return pwd_context.verify(plain_password, hashed_password)
