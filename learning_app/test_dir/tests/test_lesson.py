import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import pytest
from http import HTTPStatus
from methods.api_methods import APIS
from data.test_data import test_data

@pytest.fixture(scope='module')
def apis():
    return APIS()

def validate_response(response, expected_status, expected_message=None):
    assert response.status_code == expected_status, f"Unexpected status code: {response.status_code}, Response: {response.text}"
    if expected_message:
        assert response.json()['detail']['message'] == expected_message

# create lesson
# @pytest.mark.dependency(name="create_lesson")
# def test_create_lesson(apis):
#     payload = test_data["create_lesson"]
#     assert payload, "Missing test data for 'create_lesson'"
#     post_response = apis.post('lessons/add', payload)
#     validate_response(post_response, HTTPStatus.ok, 'Lesson added successfully')
#     print(post_response.json())


#get all lessons
@pytest.mark.dependency(name="create_lesson")
def test_get_all_lessons(apis):
    get_response = apis.get('lessons/all')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())

#get lessson by id
@pytest.mark.dependency(name="create_lesson")
def test_get_lesson_by_id(apis):
    get_all_response = apis.get('lessons/all')
    validate_response(get_all_response, HTTPStatus.OK)

    lessons = get_all_response.json().get("data", [])
    assert lessons, "No lessons found to test with"

    lesson_id = 1
    get_response = apis.get(f'lessons/{lesson_id}')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())
