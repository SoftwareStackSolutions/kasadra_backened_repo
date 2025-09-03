# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from pydantic import BaseModel, constr, EmailStr

# from learning_app.dependencies.auth_dep import get_current_user
# from learning_app.database.db import get_session
# from learning_app.models.user import User

# router = APIRouter()

# # Request schema for update
# class StudentUpdate(BaseModel):
#     Name: str
#     Email: EmailStr
#     PhoneNo: constr(pattern=r'^\d{10}$')  # must be exactly 10 digits

# @router.put("/students/update", tags=["students"])
# async def update_student_profile(
#     student_update: StudentUpdate,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user)  # JWT protection
# ):
#     # update fields
#     current_user.studentName = student_update.Name
#     current_user.Email = student_update.Email
#     current_user.PhoneNo = student_update.PhoneNo

#     db.add(current_user)
#     await db.commit()
#     await db.refresh(current_user)

#     return {
#         "status": "success",
#         "message": "Profile updated successfully",
#         "data": {
#             "id": current_user.id,
#             "Name": current_user.studentName,
#             "Email": current_user.Email,
#             "PhoneNo": current_user.PhoneNo,
#         },
#     }
