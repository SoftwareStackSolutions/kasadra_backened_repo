import requests
import pytest
from config.settings import BASE_URL

class APIS:
    def __init__(self):
        self.header = {
            "Content-Type":"application/json",
        }
        self.Prefix_URL = BASE_URL
        

    def _construct_url(self, endpoint):
        return f'{self.Prefix_URL}/{endpoint}'    
    
    def get(self,endpoint):
        response = requests.get(self._construct_url(endpoint), headers=self.header)
        return response
    
    def post(self,endpoint, data):
        response = requests.post(self._construct_url(endpoint),headers=self.header, json=data)
        return response 
    
    def put(self,endpoint, data):
        response = requests.put(self._construct_url(endpoint),headers=self.header, json=data)
        return response
    
    def delete(self,endpoint):
        response = requests.delete(self._construct_url(endpoint),headers=self.header)
        return response