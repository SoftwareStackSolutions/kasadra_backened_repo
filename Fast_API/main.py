from fastapi import FastAPI
from router import blog

app = FastAPI()
app.include_router(blog.router)
# app.include_router(blog_post.router)

@app.get('/hello')
def index():
    return {'message': 'hello world'}
