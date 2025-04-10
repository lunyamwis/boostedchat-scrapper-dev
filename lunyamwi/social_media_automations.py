import json
import requests
from .constants import LUNYAMWI_ML_BASE_URL

def send_multiple_whatsapp_messages(payload=None):
    url = LUNYAMWI_ML_BASE_URL + '/whatsapp/send-message/'
    response = None
    try:
        resp = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response = resp.json()
    except Exception as err:
        print(err)
    return response