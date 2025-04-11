from requests import Session
import json
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from time import sleep
from celery import shared_task
import os

BASE_URL = os.getenv('BASE_URL').strip()
API_VERSION = os.getenv('API_VERSION').strip()
SENDER = os.getenv('SENDER').strip()
ENDPOINT = os.getenv('ENDPOINT').strip()
API_TOKEN = os.getenv('API_TOKEN').strip()
URL = BASE_URL + API_VERSION + SENDER + ENDPOINT

def cut_string_to_max_length(input_string, max_length=912):
    if len(input_string) > max_length:
        return input_string[:max_length]
    return input_string

@shared_task
def send_batch_whatsapp_text_with_template(numbers,names,progress,paragraphs):
    # message = ' '.join(message.split())
    for i,number in enumerate(numbers):
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        parameters = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "template",
            "template": select_whatsapp_template(names[i],progress,paragraphs)

        }
        session = Session()
        session.headers.update(headers)
        try:
            response = session.post(URL, json=parameters)
            data = json.loads(response.text)
            print(f"data: {data}")
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


def select_whatsapp_template(name,progress,paragraphs):
    print(f"name========{name},progress====={progress},paragraphs======={paragraphs}")
    template = None
    if len(paragraphs) == 5:
        template = {
                "name": "truth_nugget",
                "language": {"code": "en_gb"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.ibb.co/pL5yR7C/pexels-victor-150585-448835.jpg"
                                }
                            }
                        ]  
                    },
                    
                    {
                        "type":"body",
                        "parameters":[ 
                            {
                                "type":"text",
                                "text": name,
                            },
                             {
                                "type":"text",
                                "text": progress,
                            },
                            {
                                "type":"text",
                                "text": paragraphs[0],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[1],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[2],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[3],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[4]
                            }]
                        
                    },
                    ]
                
                }
    elif len(paragraphs) == 4:
        template = {
                "name": "truth_nugget_4_paragraphs",
                "language": {"code": "en_gb"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.ibb.co/pL5yR7C/pexels-victor-150585-448835.jpg"
                                }
                            }
                        ]  
                    },
                    
                    {
                        "type":"body",
                        "parameters":[ 
                            {
                                "type":"text",
                                "text": name,
                            },
                             {
                                "type":"text",
                                "text": progress,
                            },
                            {
                                "type":"text",
                                "text": paragraphs[0],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[1],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[2],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[3],
                            },
                        ]
                    },
                    ]
                
                }
    elif len(paragraphs) == 3:
        template = {
                "name": "truth_nugget_3_paragraphs",
                "language": {"code": "en_gb"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.ibb.co/pL5yR7C/pexels-victor-150585-448835.jpg"
                                }
                            }
                        ]  
                    },
                    
                    {
                        "type":"body",
                        "parameters":[ 
                            {
                                "type":"text",
                                "text": name,
                            },
                             {
                                "type":"text",
                                "text": progress,
                            },
                            {
                                "type":"text",
                                "text": paragraphs[0],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[1],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[2],
                            },
                        ]
                    },
                    ]
                
                }
    elif len(paragraphs) == 2:
        template = {
                "name": "truth_nugget_2_paragraphs",
                "language": {"code": "en_gb"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.ibb.co/pL5yR7C/pexels-victor-150585-448835.jpg"
                                }
                            }
                        ]  
                    },
                    
                    {
                        "type":"body",
                        "parameters":[ 
                            {
                                "type":"text",
                                "text": name,
                            },
                             {
                                "type":"text",
                                "text": progress,
                            },
                            {
                                "type":"text",
                                "text": paragraphs[0],
                            },
                            {
                                "type":"text",
                                "text": paragraphs[1],
                            },
                        ]
                    },
                    ]
                
                }
    elif len(paragraphs) == 1:
        template = {
                "name": "truth_nugget_1_paragraph",
                "language": {"code": "en_gb"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.ibb.co/pL5yR7C/pexels-victor-150585-448835.jpg"
                                }
                            }
                        ]  
                    },
                    
                    {
                        "type":"body",
                        "parameters":[ 
                            {
                                "type":"text",
                                "text": name,
                            },
                             {
                                "type":"text",
                                "text": progress,
                            },
                            {
                                "type":"text",
                                "text": paragraphs[0],
                            },
                        ]
                    },
                    ]
                
                }
        
    return template


def send_batch_whatsapp_text_(numbers,names,message):
    message = ' '.join(message.split())
    for i,number in enumerate(numbers):
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        parameters = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "template",
            "template": {
                "name": "lunyamwi_birdview_template",
                "language": {"code": "en"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.postimg.cc/DwpTnkJW/boda.jpg"
                                }
                            }
                        ]  
                    },
                    {
                        "type":"body",
                        "parameters":[
                            {
                                "type":"text",
                                "text": names[i],
                            },
                            {
                                "type":"text",
                                "text": cut_string_to_max_length(message.replace("\n",""))
                            }]
                        
                    }]
                
                }

        }
        session = Session()
        session.headers.update(headers)
        try:
            response = session.post(URL, json=parameters)
            data = json.loads(response.text)
            print(f"data: {data}")
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)




@shared_task
def send_batch_whatsapp_text(numbers,names,message):
    message = ' '.join(message.split())
    for i,number in enumerate(numbers):
        
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        parameters = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "template",
            "template": {
                "name": "lunyamwi_birdview_template",
                "language": {"code": "en"},
                "components": [
                    {
                       "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                "link": "https://i.postimg.cc/DwpTnkJW/boda.jpg"
                                }
                            }
                        ]  
                    },
                    {
                        "type":"body",
                        "parameters":[
                            {
                                "type":"text",
                                "text": names[i],
                            },
                            {
                                "type":"text",
                                "text": cut_string_to_max_length(message.replace("\n",""))
                            }]
                        
                    }]
                
                }

        }
        session = Session()
        session.headers.update(headers)
        try:
            response = session.post(URL, json=parameters)
            data = json.loads(response.text)
            print(f"data: {data}")
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)



