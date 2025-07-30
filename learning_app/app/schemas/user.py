from pydantic import BaseModel, validator, EmailStr
import re

################################################
##User Register
################################################
class UserBase(BaseModel):
    username: str
    email: EmailStr
    password: str
    phonenumber : str

    @validator('phonenumber')
    def validate_phonenumber(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Please enter a valid phone number")
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # Password must be at least 8 characters long and contain at least one
        # uppercase, one lowercase, one digit, and one special character
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    

class UserDisplay(BaseModel):
    username: str
    email: str
    phonenumber : str

    class Config():
        orm_mode = True


################################################
##User Login
################################################

class UserLogin(BaseModel):
    email: EmailStr
    password: str