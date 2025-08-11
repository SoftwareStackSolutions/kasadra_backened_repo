import json
import os

# Define the path to the JSON file
json_file_path = os.path.join(os.path.dirname(__file__), 'test_data.json')

with open(json_file_path, 'r') as file:
    test_data = json.load(file)
