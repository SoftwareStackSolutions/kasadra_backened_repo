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

# create instructor
@pytest.mark.dependency("create_instructor")
def test_create_instructor(apis):
    payload = test_data["create_instructor"]
    assert payload, "Missing test data for 'create_instructor'"
    post_response = apis.post('instructor/create', payload)
    validate_response(post_response, HTTPStatus.OK, 'Instructor created successfully')

#login instructor
@pytest.mark.dependency("create_instructor")
def test_login_instructor(apis):
    payload = test_data["instructor_login"]
    assert payload, "Missing test data for 'login_instructor'"
    post_response = apis.post('instructor/login', payload)
    validate_response(post_response, HTTPStatus.OK, 'Logged in successfully')

#get all instructors
@pytest.mark.dependency("create_instructor")
def test_get_all_instructors(apis):
    get_response = apis.get('instructor/all')
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json()) 