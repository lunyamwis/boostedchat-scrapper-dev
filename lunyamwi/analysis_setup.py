import requests
import os
import json
from .constants import LUNYAMWI_ML_BASE_URL

def get_sql_records(payload=None):
    url = LUNYAMWI_ML_BASE_URL + '/api/get_sql_records/'
    response = None
    try:
        resp = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response = resp.json()
    except Exception as err:
        print(err)
    return response

def get_sql_records_by_id(payload=None, id=None):
    url = LUNYAMWI_ML_BASE_URL + f'/api/get_sql/{id}/'
    response = None
    try:
        resp = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response = resp.json()
    except Exception as err:
        print(err)
    return response

def select_and_export_charts(payload=None):
    url = LUNYAMWI_ML_BASE_URL + '/api/dashboard/'
    response = None
    try:
        resp = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response = resp.json()
    except Exception as err:
        print(err)
    return response