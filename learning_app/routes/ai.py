from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

# router = APIRouter()

# client = OpenAI(api_key="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")

# class AskRequest(BaseModel):
#     message: str

# @router.post("/api/ask-ai", tags=["chat bot"])
# async def ask_ai(req: AskRequest):
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "user", "content": req.message}
#         ]
#     )

#     # FIX: use .content instead of ["content"]
#     answer = response.choices[0].message.content
    
#     return {"reply": answer}


from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key="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")

class DescriptionRequest(BaseModel):
    course_title: str

@router.post("/api/ask-ai", tags=["chat bot"])
async def generate_description(req: DescriptionRequest):
    prompt = f"""
    Write a VERY SHORT course description (1–2 lines only).

    Course Title: {req.course_title}

    Rules:
    - Maximum 25 words
    - Simple and professional
    - Beginner friendly
    - Plain text only
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    description = response.choices[0].message.content
    return {"description": description}
