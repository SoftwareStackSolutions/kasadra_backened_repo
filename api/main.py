from fastapi import FastAPI
from Fast_API.api.router import blog
from router import blog_post

app = FastAPI()
app.include_router(blog.router)
app.include_router(blog_post.router)

@app.get('/hello')
def index():
    return {'message': 'hello world'}