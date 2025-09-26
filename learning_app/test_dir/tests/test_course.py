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
    assert response.status_code == expected_status, \
        f"Unexpected status code: {response.status_code}, Response: {response.text}"
    if expected_message:
        data = response.json()
        assert data.get("message") == expected_message, \
            f"Unexpected message: {data.get('message')}, Response: {data}"


# create course
@pytest.mark.dependency(name="create_course")
def test_create_course(apis):
    payload = test_data["create_course"]
    assert payload, "Missing test data for 'create_course'"
    post_response = apis.post('courses/add', payload)
    validate_response(post_response, HTTPStatus.OK, 'Course added successfully')


#get all courses
def test_get_all_courses(apis):
    get_response = apis.get('courses/all')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())

#get course by id
def test_get_course_by_id(apis):
    get_all_response = apis.get('courses/all')
    validate_response(get_all_response, HTTPStatus.OK)
    courses = get_all_response.json().get("data", [])
    assert courses, "No courses found to test with"

    course_id = 1   # take the first course
    get_response = apis.get(f'courses/{course_id}')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())
