import requests
import json

def createDummyData(filePath:str, url:str = ''):

    with open(filePath) as f:
        data = json.load(f)
        for entry in data:
            response = requests.post(url,data=entry)
            print('\n' + str(response.json()))


createDummyData('dummyData/USERS_MOCK_DATA.json', 'http://127.0.0.1:8000/auth/users/')