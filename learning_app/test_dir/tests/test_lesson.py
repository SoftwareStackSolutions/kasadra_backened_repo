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
#get all lessons
def test_get_all_lessons(apis):
    get_response = apis.get('api/lessons/all')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())

#get lessson by id
def test_get_lesson_by_id(apis):
    get_all_response = apis.get('api/lessons/all')
    validate_response(get_all_response, HTTPStatus.OK)

    lessons = get_all_response.json().get("data", [])
    assert lessons, "No lessons found to test with"

    lesson_id = 3
    get_response = apis.get(f'api/lessons/{lesson_id}')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())
