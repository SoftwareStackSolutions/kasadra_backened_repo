import sys
import os

# Add parent dir (Fast_API) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.router.blog import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_index():
    response = client.get("/blog/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world!"}

def test_get_all_blogs():
    response = client.get("/blog/all")
    assert response.status_code == 200
    assert response.json() == {"message": "All blogs provided"}

def test_get_comment_defaults():
    response = client.get("/blog/1/comments/2")
    assert response.status_code == 200
    assert response.json() == {"message": "blog_id 1, comment_id 2, valid True, username None"}

def test_get_comment_with_query_params():
    response = client.get("/blog/1/comments/2?valid=false&username=alice")
    assert response.status_code == 200
    assert response.json() == {"message": "blog_id 1, comment_id 2, valid False, username alice"}

def test_get_blog_type_valid():
    for blog_type in ['short', 'story', 'howto']:
        response = client.get(f"/blog/type/{blog_type}")
        assert response.status_code == 200
        assert response.json() == {"message": f"Blog type {blog_type}"}

def test_get_blog_type_invalid():
    response = client.get("/blog/type/invalidtype")
    assert response.status_code == 422  # validation error for invalid enum

def test_get_blog_found():
    response = client.get("/blog/3")
    assert response.status_code == 200
    assert response.json() == {"message": "Blog with id 3"}

def test_get_blog_not_found():
    response = client.get("/blog/10")
    assert response.status_code == 404
    assert response.json() == {"error": "Blog 10 not found"}


