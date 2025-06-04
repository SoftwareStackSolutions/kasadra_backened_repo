from fastapi import APIRouter, status, Response
from enum import Enum
from typing import Optional

router = APIRouter(
    prefix='/blog',
    tags=['blog']
)

@router.get('/hello')
def index():
    return {'message': 'hello world!'}

@router.get('/all')
def get_all_blogs():
    return {'message': 'All blogs provided'}

@router.get('/{id}/comments/{comment_id}')
def get_comment(id: int, comment_id: int, valid: bool = True, username: Optional[str] = None):
    return {'message': f'blog_id {id}, comment_id {comment_id}, valid {valid}, username {username}'}

class BlogeType(str, Enum):
    short = 'short'
    story = 'story'
    howto = 'howto'

@router.get('/type/{type}')
def get_blog_type(type: BlogeType):
    return {'message': f'Blog type {type.value}'}


@router.get('/{id}', status_code=status.HTTP_200_OK)
def get_blog(id: int, response: Response):
    if id > 5:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': f'Blog {id} not found'}
    else:
        return {'message': f'Blog with id {id}'}

def test_summary():
    return {'message': 'hello world!'}
