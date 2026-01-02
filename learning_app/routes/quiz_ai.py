# from pydantic import BaseModel
# from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
# from database.db import get_session
# from dependencies.auth_dep import get_current_user
# from models.user import User, RoleEnum
# from models.course import Course, Note, Lesson


# class AIQuizCreate(BaseModel):
#     course_id: int
#     lesson_id: int
#     topic: str
#     num_questions: int = 10

# from fastapi import APIRouter
# from pydantic import BaseModel
# from openai import OpenAI
# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def build_quiz_prompt(topic: str, count: int):
#     return f"""
# Create {count} multiple choice questions for the topic "{topic}".

# Rules:
# - Each question must have exactly 4 options
# - Correct answer must be one of A, B, C, D
# - Return ONLY valid JSON
# - No explanation text

# JSON format:
# {{
#   "questions": [
#     {{
#       "question": "...",
#       "options": {{
#         "A": "...",
#         "B": "...",
#         "C": "...",
#         "D": "..."
#       }},
#       "correct": "A"
#     }}
#   ]
# }}
# """

# @router.post("/quizzes/ai-generate", tags=["AI Quiz"])
# async def generate_ai_quiz(
#     payload: AIQuizCreate,
#     db: AsyncSession = Depends(get_session),
#     instructor: User = Depends(get_current_instructor)
# ):
#     # 1. Validate course & lesson
#     course = await db.get(Course, payload.course_id)
#     if not course:
#         raise HTTPException(404, "Course not found")

#     lesson = await db.get(Lesson, payload.lesson_id)
#     if not lesson or lesson.course_id != course.id:
#         raise HTTPException(400, "Invalid lesson")

#     # 2. Call OpenAI
#     prompt = build_quiz_prompt(payload.topic, payload.num_questions)

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.3
#     )

#     try:
#         ai_data = json.loads(response.choices[0].message.content)
#     except Exception:
#         raise HTTPException(500, "AI returned invalid JSON")

#     questions = ai_data.get("questions", [])
#     if not questions:
#         raise HTTPException(400, "No questions generated")

#     # 3. Create Quiz
#     quiz = Quiz(
#         course_id=payload.course_id,
#         lesson_id=payload.lesson_id,
#         name=f"Quiz: {payload.topic}",
#         description=f"AI generated quiz on {payload.topic}"
#     )
#     db.add(quiz)
#     await db.flush()  # get quiz.id

#     # 4. Save Questions
#     for q in questions:
#         qq = QuizQuestion(
#             quiz_id=quiz.id,
#             question=q["question"],
#             option_a=q["options"]["A"],
#             option_b=q["options"]["B"],
#             option_c=q["options"]["C"],
#             option_d=q["options"]["D"],
#             correct_option=q["correct"]
#         )
#         db.add(qq)

#     await db.commit()

#     return {
#         "status": "success",
#         "message": "Quiz generated successfully",
#         "quiz_id": quiz.id,
#         "total_questions": len(questions)
#     }

# #####################
# ## GEt 
# #####################

# @router.get("/student/quizzes/{quiz_id}")
# async def get_quiz_for_student(
#     quiz_id: int,
#     db: AsyncSession = Depends(get_session)
# ):
#     quiz = await db.get(Quiz, quiz_id)
#     if not quiz:
#         raise HTTPException(404, "Quiz not found")

#     questions = (await db.execute(
#         select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
#     )).scalars().all()

#     return {
#         "quiz_id": quiz.id,
#         "quiz_name": quiz.name,
#         "questions": [
#             {
#                 "id": q.id,
#                 "question": q.question,
#                 "options": {
#                     "A": q.option_a,
#                     "B": q.option_b,
#                     "C": q.option_c,
#                     "D": q.option_d
#                 }
#             }
#             for q in questions
#         ]
#     }
