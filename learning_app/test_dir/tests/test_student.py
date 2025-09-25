import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import pytest
from http import HTTPStatus
from methods.api_methods import APIS
from data.test_data import test_data
from datetime import datetime

@pytest.fixture(scope='module')
def apis():
    return APIS()



def validate_response(response, expected_status, expected_message=None):
    assert response.status_code == expected_status, f"Unexpected status code: {response.status_code}, Response: {response.text}"
    if expected_message:
        assert response.json()['detail']['message'] == expected_message


@pytest.mark.dependency(name="create_student")
def test_create_student(apis):
    
    
    payload = test_data["create_student"].copy()
    payload["created_at"] = datetime.utcnow().date().isoformat()  # <-- only YYYY-MM-DD
    assert payload, "Missing test data for 'create_student'"
    post_response = apis.post('student/create', payload)
    validate_response(post_response, HTTPStatus.OK, 'Student created successfully')

#login student
@pytest.mark.dependency(name="create_student")
def test_login_student(apis):
    payload = test_data["student_login"]
    # assert payload, "Missing test data for 'login_student'"
    post_response = apis.post('student/login', payload)
    validate_response(post_response, HTTPStatus.OK, "Logged in successfully")
    print(post_response.json())

#get all students
# def test_get_allstudents(apis):
#     get_response = apis.get('api/student/all')
#     validate_response(get_response, HTTPStatus.OK)
#     print(get_response.json())        

# create student