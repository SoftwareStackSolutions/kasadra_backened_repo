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
@pytest.mark.dependency(name="add_calander")
def test_create_schedule_class(apis):
    payload = test_data["add_calendar"]
    assert payload, "Missing test data for 'add_calendar'"
    post_response = apis.post('scheduleclass/add', payload)
    validate_response(post_response, HTTPStatus.OK, 'schedule created successfully')


#get all schedule classes
def test_get_all_schedule_classes(apis):
    get_response = apis.get('scheduleclass/view/7')  # Assuming course_id=1 for testing
    validate_response(get_response, HTTPStatus.OK)
    print(get_response.json())

# update schedule class
@pytest.mark.dependency(depends=["add_calander"])
def test_update_schedule_class(apis):               
    payload = test_data["update_calendar"]
    assert payload, "Missing test data for 'update_calendar'"
    put_response = apis.put(f'scheduleclass/update/2', payload)
    validate_response(put_response, HTTPStatus.OK, 'Schedule class updated successfully')

# delete schedule class
@pytest.mark.dependency(depends=["add_calander"])   
def test_delete_schedule_class(apis):
    calendar_id =6  # Assuming calendar_id=1 for testing
    delete_response = apis.delete(f'scheduleclass/delete/{calendar_id}')
    validate_response(delete_response, HTTPStatus.OK, 'Schedule class deleted successfully')