import random
import json
import requests
import uuid
import logging

import os
import re
import time
import ast
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_tenants.utils import schema_context
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import AllowAny

from api.whatsapp.models import ChatSession
from .prompts import hospital_prompt, system_prompt,solarama_prompt
from .tasks import send_batch_whatsapp_text
from .constants import GROUPS_TO_REACT_TO

load_dotenv()

# Whapi.cloud Configuration
WHAPI_BASE_URL = os.getenv("WHAPI_BASE_URL", "https://example.com")
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN","test_token")  # Add this to your .env file
WHAPI_HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {WHAPI_TOKEN}",
    "Content-Type": "application/json"
}




# Constants
messaging_url = f"https://graph.facebook.com/v18.0/{settings.PHONE_NUMBER_ID}/messages"
auth_header = {"Authorization": f"Bearer {settings.ACCESS_TOKEN}"}
messaging_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
}

created_flow_id = ""


# from llama_cpp import Llama # Removed as it's not used in the provided code

load_dotenv()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
TOKEN = os.getenv("TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
code_prompt_texts = ["Contact us", "Chat with our chatbot", "YES", "NO"]

service_list = [
    "Evacuation and Repatriation Insurance",
    "Personal Accident Insurance",
    "Medical Expenses Insurance",
    "Last Expense Insurance",
]




class SendBatchWhatsAppView(APIView):
    def post(self, request):
        try:
            data = None
            if not request.data:
                return Response({"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST)

            
            content = request.data.get('_content')
            if content is None:
                logging.warning({"error": f"'_content' not found in request data - {request.data}"})
            else:
                logging.info(content)
                

            try:
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = request.data
            except json.JSONDecodeError as e:
                return Response({"error": "Invalid JSON data"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            numbers = data.get('numbers', [])
            if isinstance(numbers, str):
                numbers = ast.literal_eval(numbers)
            names = data.get('names', [])
            if isinstance(names, str):
                names = ast.literal_eval(names)
            progress = data.get('progress', False)
            paragraphs = data.get('paragraphs','')
            
            # get more into detail

            if not numbers or not names or not paragraphs:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            if len(numbers) != len(names):
                return Response({"error": "Numbers and names lists must be of equal length"}, status=status.HTTP_400_BAD_REQUEST)

            send_batch_whatsapp_text.delay(numbers, names, paragraphs)
            return Response({"message": "Task initiated successfully"}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logging.warning({"error": f"An error occurred - {str(e)}"})
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def webhook(request):
    if request.method == 'GET':
        print(request.GET)
        # Verification
        # Check if the request is a verification request
        if (request.GET.get("hub.mode") == "subscribe" and
            request.GET.get("hub.verify_token") == TOKEN):
            challenge = request.GET.get("hub.challenge")
            print(challenge)
            # return Response(challenge, status=status.HTTP_200_OK)
            # return JsonResponse({"challenge": challenge}, status=status.HTTP_200_OK)
            return HttpResponse(challenge, status=200)
            # return {"challenge":challenge,"status":200}
        else:
            # return Response("Verification failed", status=status.HTTP_403_FORBIDDEN)
            # return JsonResponse({"message": "Verification failed", "status": 403})
            return HttpResponse("Verification failed", status=403)
            # return {"message":"Verification failed","status":403}

    elif request.method == 'POST':
        logging.warning(request.data)
        request_data = request.data  # Access POST data via request.data
        logging.warning(request_data)
        
        if (request_data['entry'][0]['changes'][0]['value'].get('messages') is not None):
            name = request_data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']

            if (request_data['entry'][0]['changes'][0]['value']['messages'][0].get('text') is not None):
                message = request_data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
                user_phone_number = request_data['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
                user_message_processor(message, user_phone_number, name)

            elif (request_data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['nfm_reply']['response_json'] is not None):
                # Process flow reply
                flow_reply_processor(request_data) # Pass the parsed data
            
        return Response("PROCESSED", status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def query_gpt_test(request):
    # print("hahahahahahahahahahhaha--------------------")
    if request.method == 'GET':
        print(request.GET)
        prompt = "Hello, how are you?"
        phone = generate_test_phone_number()
        chat_session= None
        res = None
        
        try:
            # Check if session exists
            chat_session = ChatSession.objects.get(phone=phone)
            chat_session.add_message("user", prompt)
        except ChatSession.DoesNotExist:
            conversation_history=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
            chat_session = ChatSession.objects.create(
                phone=phone,
                conversation_history=conversation_history
            )
        body = {
            "model": "gpt-4-1106-preview",
            "messages": chat_session.conversation_history,
        }
        header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

        res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
        logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))
        
        chat_session.add_message("system", res.json()["choices"][0]["message"]["content"])
        api_response = {
            "response": res.json()["choices"][0]["message"]["content"],
            phone: phone,
            "conversation_history": chat_session.conversation_history,
            
        }
        return Response(api_response,status=status.HTTP_200_OK) 
    
    elif request.method == 'POST':
        # print("THis is a a post request",request.data)
        my_prompt = request.data.get('prompt')
        phone = request.data.get('phone')
        chat_session=None
        
        new_message = {"role": "user", "content": my_prompt}

        try:
            # Check if session exists
            chat_session = ChatSession.objects.get(phone=phone)
            chat_session.add_message(new_message["role"], new_message["content"])
        except ChatSession.DoesNotExist:
            print("wooooooiiiiii")
            conversation_history=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": my_prompt},
                ]
            chat_session = ChatSession.objects.create(
                phone=phone,
                conversation_history=conversation_history
            )

        body = {
            "model": "gpt-4-1106-preview",
            "messages": chat_session.conversation_history,
        }
        header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

        res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
        logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))
        
        
       
        chat_session.add_message("system", res.json()["choices"][0]["message"]["content"])
        api_response = {
            "response": res.json()["choices"][0]["message"]["content"],
            phone: phone,
            "conversation_history": chat_session.conversation_history,    
        }
        return Response(api_response, status=status.HTTP_200_OK) 
        

def flow_reply_processor(request_data):  # Modified to accept parsed data
    name = request_data['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
    message = request_data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['nfm_reply']['response_json']

    flow_message = json.loads(message)
    flow_key = flow_message["flow_key"]

    if flow_key == "agentconnect":
        firstname = flow_message["firstname"]
        reply = f"Thank you for reaching out {firstname}. An agent will reach out to you the soonest"
    else:
        firstname = flow_message["firstname"]
        secondname = flow_message["secondname"]
        issue = flow_message["issue"]
        reply = f"Your response has been recorded. This is what we received:\n\n*NAME*: {firstname} {secondname}\n*YOUR MESSAGE*: {issue}"

    user_phone_number = request_data['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    send_message(reply, user_phone_number, "FLOW_RESPONSE", name)


def extract_string_from_reply(user_input):
    if user_input == "1":
        user_prompt = code_prompt_texts[0].lower()
    elif user_input == "2":
        user_prompt = code_prompt_texts[1].lower()
    elif user_input == "Y":
        user_prompt = code_prompt_texts[2].lower()
    elif user_input == "N":
        user_prompt = code_prompt_texts[3].lower()
    else:
        user_prompt = str(user_input).lower()

    return user_prompt


def user_message_processor(message, phonenumber, name):
    
    send_message(message, phonenumber, "CHATBOT", name)
    # We are not using this for now, we don't want to intercept the
    # type of messages the client sends. we want to process all messages
    
    # user_prompt = extract_string_from_reply(message)
    # if user_prompt == "yes":
    #     send_message(message, phonenumber, "TALK_TO_AN_AGENT", name)
    # elif user_prompt == "no":
    #     print("Chat terminated")
    # else:
    #     if re.search("hello|hi|greetings", user_prompt):
            
    #         if re.search("this", user_prompt):
    #             send_message(message, phonenumber, "CHATBOT", name)

    #         else:
    #             print(user_prompt)
    #             send_message(message, phonenumber, "SEND_GREETINGS_AND_PROMPT", name)

    #     else:
    #         send_message(message, phonenumber, "CHATBOT", name)
    
@schema_context(os.getenv('SCHEMA_NAME'))
def query_gpt(prompt,phone_number=None):
    # declare chat_session variable
    chat_session= None
    if phone_number is not None:
        try:
            # Check if session exists
            conversation_history=[
                {"role": "system", "content": solarama_prompt},
                {"role": "user", "content": prompt},
            ]
            chat_session = ChatSession.objects.get(phone=phone_number)
            chat_session.conversation_history = conversation_history
            chat_session.save()
            chat_session.add_message("user", prompt)
        except ChatSession.DoesNotExist:
            conversation_history=[
                    {"role": "system", "content": solarama_prompt},
                    {"role": "user", "content": prompt},
                ]
            chat_session = ChatSession.objects.create(
                phone=phone_number,
                conversation_history=conversation_history
            )
    body = {
        "model": "gpt-4-1106-preview",
        "messages": chat_session.conversation_history,
    }
    header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

    res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
    # save the response to the database
    gpt_response = res.json()["choices"][0]["message"]["content"]
    chat_session.add_message("system", gpt_response)
    logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))

    return res.json()

def send_message(message, phone_number, message_option, name):
    print(phone_number)
    greetings_text_body = (
        "\nHello "
        + name
        + ". Welcome to our Chatbot. What would you like us to help you with?\nPlease respond with a numeral between 1 and 2.\n\n1. "
        + code_prompt_texts[0]
        + "\n2. "
        + code_prompt_texts[1]
        + "\n\nAny other reply will connect you with our chatbot."
    )

    services_list_text = ""
    for i in range(len(service_list)):
        item_position = i + 1
        services_list_text = (
            f"{services_list_text} {item_position}. {service_list[i]} \n"
        )

    service_intro_text = f"We offer a range of services to ensure a comfortable stay, including but not limited to:\n\n{services_list_text}\n\nWould you like to connect with an agent to get more information about the services?\n\nY: Yes\nN: No"

    contact_flow_payload = flow_details(
        flow_header="Contact Us",
        flow_body="You have indicated that you would like to contact us.",
        flow_footer="Click the button below to proceed",
        flow_id=str("<FLOW-ID>"),
        flow_cta="Proceed",
        recipient_phone_number=phone_number,
        screen_id="CONTACT_US",
    )

    agent_flow_payload = flow_details(
        flow_header="Talk to an Agent",
        flow_body="You have indicated that you would like to talk to an agent to get more information about the services that we offer.",
        flow_footer="Click the button below to proceed",
        flow_id=str("<FLOW-ID>"),
        flow_cta="Proceed",
        recipient_phone_number=phone_number,
        screen_id="TALK_TO_AN_AGENT",
    )

    if message_option == "SEND_GREETINGS_AND_PROMPT":
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "text",
                "text": {"preview_url": False, "body": greetings_text_body},
            }
        )
    elif message_option == "SERVICE_INTRO_TEXT":
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "text",
                "text": {"preview_url": False, "body": service_intro_text},
            }
        )
    elif message_option == "CHATBOT":
        output_message = query_gpt(message,phone_number)["choices"][0]["message"]["content"]
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body":  output_message,
                },
            }
        )
    elif message_option == "CONTACT_US":
        payload = contact_flow_payload
    elif message_option == "TALK_TO_AN_AGENT":
        payload = agent_flow_payload
    elif message_option == "FLOW_RESPONSE":
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": str(phone_number),
                "type": "text",
                "text": {"preview_url": False, "body": message},
            }
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + ACCESS_TOKEN,
    }

    resp = requests.request("POST", WHATSAPP_URL, headers=headers, data=payload)
    print(resp.json())
    print("MESSAGE SENT")


def flow_details(
    flow_header,
    flow_body,
    flow_footer,
    flow_id,
    flow_cta,
    recipient_phone_number,
    screen_id,
):
    flow_token = str(uuid.uuid4())

    flow_payload = json.dumps(
        {
            "type": "flow",
            "header": {"type": "text", "text": flow_header},
            "body": {"text": flow_body},
            "footer": {"text": flow_footer},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": flow_token,
                    "flow_id": flow_id,
                    "flow_cta": flow_cta,
                    "flow_action": "navigate",
                    "flow_action_payload": {"screen": screen_id},
                },
            },
        }
    )

    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": str(recipient_phone_number),
            "type": "interactive",
            "interactive": json.loads(flow_payload),
        }
    )
    return payload

class CreateFlowView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        flow_base_url = (
            f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/flows"
        )
        flow_creation_payload = {"name": "<FLOW-NAME>", "categories": '["SURVEY"]'}
        flow_create_response = requests.post(
            flow_base_url, headers=auth_header, json=flow_creation_payload
        )

        try:
            global created_flow_id
            created_flow_id = flow_create_response.json()["id"]
            graph_assets_url = f"https://graph.facebook.com/v18.0/{created_flow_id}/assets"

            upload_flow_json(graph_assets_url)
            publish_flow(created_flow_id)

            return Response({"message": "FLOW CREATED"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class WebhookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if (
            request.GET.get("hub.mode") == "subscribe"
            and request.GET.get("hub.verify_token") == settings.VERIFY_TOKEN
        ):
            return Response(request.GET.get("hub.challenge"), status=200)
        else:
            return Response({"message": "Failed verification"}, status=403)

    def post(self, request):
        data = request.data

        if data["entry"][0]["changes"][0]["value"].get("messages") is not None:
            if data["entry"][0]["changes"][0]["value"]["messages"][0].get("text") is not None:
                user_phone_number = data["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
                send_flow(created_flow_id, user_phone_number)
            else:
                flow_reply_processor_(data)

        return Response({"message": "PROCESSED"}, status=200)


def flow_reply_processor_(data):
    flow_response = data["entry"][0]["changes"][0]["value"]["messages"][0]["interactive"]["nfm_reply"]["response_json"]
    flow_data = json.loads(flow_response)
    # Process flow_data as needed...

    reply = "Thanks for taking the survey! Your response has been recorded."
    user_phone_number = data["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    send_message_flow(reply, user_phone_number)


def send_message_flow(message, phone_number):
    payload = {
        "messaging_product": "whatsapp",
        "to": str(phone_number),
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    requests.post(messaging_url, headers=messaging_headers, json=payload)


def upload_flow_json(graph_assets_url):
    files = {"file": ("survey.json", open("survey.json", "rb"), "application/json")}
    res = requests.post(graph_assets_url, headers=auth_header, files=files)
    print(res.json())


def publish_flow(flow_id):
    flow_publish_url = f"https://graph.facebook.com/v18.0/{flow_id}/publish"
    requests.post(flow_publish_url, headers=auth_header)


def send_flow(flow_id, recipient_phone_number):
    flow_token = str(uuid.uuid4())
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(recipient_phone_number),
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {"type": "text", "text": "Survey"},
            "body": {
                "text": (
                    "Your insights are invaluable to us – please take a moment to share your feedback in our survey."
                )
            },
            "footer": {"text": "Click the button below to proceed"},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": flow_token,
                    "flow_id": flow_id,
                    "flow_cta": "Proceed",
                    "flow_action_payload": {"screen": "SURVEY_SCREEN"},
                },
            },
        },
    }
    requests.post(messaging_url, headers=messaging_headers, json=payload)

# This function generates a test phone number in the format "test-2547XXXXXXXX"
def generate_test_phone_number():
    # Generate 8 random digits
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"test-2547{random_digits}"



# Helper function for making Whapi requests

def make_whapi_request(method: str, endpoint: str, params: Dict = None, data: Dict = None, headers: Dict = None) -> Dict:
    """Helper function to make requests to Unipile API"""
    url = f"{WHAPI_BASE_URL}{endpoint}"
    # print(url)

    request_headers = WHAPI_HEADERS.copy()
    if headers:
        request_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=request_headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=request_headers, params=params, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=request_headers, params=params, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=request_headers, params=params)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=request_headers, params=params, json=data)
        else:
            return {"success": False, "error": "Unsupported HTTP method", "status_code": 400}
        
        return {
            "success": response.ok,
            "data": response.json() if response.content else {},
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
        }
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}


class ChannelHealthView(APIView):
    """Check health & launch channel"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/health")
        return Response(result, status=result.get('status_code', 500))

class ChannelSettingsView(APIView):
    """Manage channel settings"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get channel settings"""
        result = make_whapi_request("GET", "/settings")
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request):
        """Update channel settings"""
        result = make_whapi_request("PATCH", "/settings", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request):
        """Reset channel settings"""
        result = make_whapi_request("DELETE", "/settings")
        return Response(result, status=result.get('status_code', 500))

class ChannelEventsView(APIView):
    """Get allowed events"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/settings/events")
        return Response(result, status=result.get('status_code', 500))

class WebhookTestView(APIView):
    """Test webhook"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/settings/webhook_test", data=request.data)
        return Response(result, status=result.get('status_code', 500))


def extract_from_number(message_data):
    """
    Extracts the 'from' number from the first message in the provided data.

    Args:
        message_data (dict): The dictionary containing message details.

    Returns:
        str or None: The 'from' number if found, else None.
    """
    if 'messages' not in message_data:
        return None
    
    try:
        messages = message_data['messages']
        if messages and len(messages) > 0:
            from_number = messages[0].get('from')
            return from_number
        return None
    except (AttributeError, IndexError):
        return None

def extract_group_name(message_data):
    """
    Extracts the group name from the provided message data.

    Args:
        message_data (dict): The dictionary containing message details.

    Returns:
        str or None: The group name if found, else None.
    """
    if 'messages' not in message_data:
        return None
    
    try:
        messages = message_data['messages']
        if messages and len(messages) > 0:
            group_name = messages[0].get('chat_name')
            return group_name
        return None
    except (AttributeError, IndexError):
        return None


def extract_message_body(message_data):
    """
    Extracts the message body from the provided message data.

    Args:
        message_data (dict): The dictionary containing message details.

    Returns:
        str or None: The message body if found, else None.
    """
    if 'messages' not in message_data:
        return None
    
    try:
        messages = message_data['messages']
        if messages and len(messages) > 0:
            message_body = messages[0].get('text', {}).get('body')
            return message_body
        return None
    except (AttributeError, IndexError):
        return None


@api_view(['GET', 'POST'])
@schema_context(os.getenv('SCHEMA_NAME'))
def webhook_whapi(request):
    if request.method == 'GET':
        print(request.GET)
        return Response({"message": "Webhook GET request received"}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        print(request.data)
        # Example usage:

        number = extract_from_number(request.data)
        group_name = extract_group_name(request.data)
        message = extract_message_body(request.data)
        print("Message:", message)
        print("From number:", number)
        if group_name in GROUPS_TO_REACT_TO:
            generated_message = query_gpt(message, number)["choices"][0]["message"]["content"]
            time.sleep(15)  # Simulate typing delay
            make_whapi_request("POST", "/messages/text", data = {
                "typing_time": 0,
                "to": number,
                "body": generated_message
            })
        elif ChatSession.objects.filter(phone=number).exists():
            response = query_gpt(message, number)["choices"][0]["message"]["content"]
            time.sleep(15)  # Simulate typing delay
            make_whapi_request("POST", "/messages/text", data = {
                "typing_time": 0,
                "to": number,
                "body": response
            })
        
        # Process the webhook data here
        # You can call your processing function or save the data to the database
        # For example:
        # process_webhook_data(request.data)
        return Response({"message": "Webhook POST request received"}, status=status.HTTP_200_OK)
    return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



class WhatsAppAuthURLView(APIView):
    def get(self, request):
        client_id = os.getenv("WHATSAPP_CLIENT_ID")
        redirect_uri = os.getenv("WHATSAPP_REDIRECT_URI")
        scope = "whatsapp_business_management"

        auth_url = (
            f"https://www.facebook.com/v20.0/dialog/oauth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_type=code"
        )
        return Response({"auth_url": auth_url})

class WhatsAppOAuthCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response(
                {"error": "Missing code parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
        data = {
            "client_id": os.getenv("WHATSAPP_CLIENT_ID"),
            "client_secret": os.getenv("WHATSAPP_CLIENT_SECRET"),
            "code": code,
            "redirect_uri": os.getenv("WHATSAPP_REDIRECT_URI"),
        }

        response = requests.get(token_url, params=data)  # <-- Graph API expects GET, not POST
        if response.status_code != 200:
            return Response(
                {"error": response.json()},
                status=response.status_code
            )

        token_data = response.json()
        access_token = token_data.get("access_token")

        # TODO: Save token in DB associated with the user
        return Response({"access_token": access_token})


class ChannelLimitsView(APIView):
    """Get limits"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/limits")
        return Response(result, status=result.get('status_code', 500))


class UserLoginView(APIView):
    """User login endpoints"""
    permission_classes = [AllowAny]
    
    def get(self, request, phone_number=None):
        if phone_number:
            # Get auth code by phone number
            endpoint = f"/users/login/{phone_number}"
        else:
            # Login user with QR-base64
            endpoint = "/users/login"
        
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class UserLogoutView(APIView):
    """Logout user"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/users/logout", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class UserProfileView(APIView):
    """User profile management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get user info"""
        result = make_whapi_request("GET", "/users/profile")
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request):
        """Update user info"""
        result = make_whapi_request("PATCH", "/users/profile", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class UserInfoView(APIView):
    """Query account information"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        contact_id = request.data.get('contact_id')
        if not contact_id:
            return Response({"error": "contact_id query parameter is required"}, status=400)

        result = make_whapi_request("GET", f"/contacts/{contact_id}/profile")
        return Response(result, status=result.get('status_code', 500))

# class UserGDPRView(APIView):
#     """GDPR account report"""
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         """Request GDPR account report"""
#         result = make_whapi_request("POST", "/users/gdpr", data=request.data)
#         return Response(result, status=result.get('status_code', 500))
    
#     def get(self, request):
#         """Get GDPR report status"""
#         result = make_whapi_request("GET", "/users/gdpr")
#         return Response(result, status=result.get('status_code', 500))

class UserStatusView(APIView):
    """Change status text"""
    permission_classes = [AllowAny]
    
    def put(self, request):
        result = make_whapi_request("PUT", "/status", data=request.data)
        return Response(result, status=result.get('status_code', 500))


class MessagesListView(APIView):
    """Get messages"""
    permission_classes = [AllowAny]
    
    def get(self, request, chat_id=None):
        if chat_id:
            endpoint = f"/messages/list/{chat_id}"
        else:
            endpoint = "/messages/list"
        
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class SendTextMessageView(APIView):
    """Send text message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/text", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendImageMessageView(APIView):
    """Send media-image message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/image", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendVideoMessageView(APIView):
    """Send media-video message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/video", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendShortVideoMessageView(APIView):
    """Send media-short video message (PTV)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/short", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendGifMessageView(APIView):
    """Send media-gif message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/gif", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendAudioMessageView(APIView):
    """Send media-audio message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/audio", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendVoiceMessageView(APIView):
    """Send media-voice message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/voice", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendDocumentMessageView(APIView):
    """Send media-document message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/document", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendLinkPreviewMessageView(APIView):
    """Send link preview message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/link_preview", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendLocationMessageView(APIView):
    """Send location message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/location", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendLiveLocationMessageView(APIView):
    """Send live location message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/live_location", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendContactMessageView(APIView):
    """Send contact message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/contact", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendContactListMessageView(APIView):
    """Send contact list message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/contact_list", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendPollMessageView(APIView):
    """Send poll message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/poll", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendInteractiveMessageView(APIView):
    """Send interactive message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/interactive", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendStickerMessageView(APIView):
    """Send media-sticker message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/sticker", data=request.data)
        return Response(result, status=result.get('status_code', 500))

# Story message endpoints
class SendStoryMessageView(APIView):
    """Send story message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/story", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendStoryAudioMessageView(APIView):
    """Send story audio message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/story/audio", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendStoryMediaMessageView(APIView):
    """Send story media message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/story/media", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendStoryTextMessageView(APIView):
    """Send story text message"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/messages/story/text", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class SendMediaMessageView(APIView):
    """Send media message"""
    permission_classes = [AllowAny]
    
    def post(self, request, media_type):
        endpoint = f"/messages/media/{media_type}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

# Message management endpoints
class MessageView(APIView):
    """Message management"""
    permission_classes = [AllowAny]
    
    def get(self, request, message_id):
        """Get message"""
        endpoint = f"/messages/{message_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, message_id):
        """Forward message"""
        endpoint = f"/messages/{message_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request, message_id):
        """Mark message as read"""
        endpoint = f"/messages/{message_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, message_id):
        """Delete message"""
        endpoint = f"/messages/{message_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class MessageReactionView(APIView):
    """Message reaction management"""
    permission_classes = [AllowAny]
    
    def put(self, request, message_id):
        """React to message"""
        endpoint = f"/messages/{message_id}/reaction"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, message_id):
        """Remove react from message"""
        endpoint = f"/messages/{message_id}/reaction"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class MessageStarView(APIView):
    """Star message"""
    permission_classes = [AllowAny]
    
    def put(self, request, message_id):
        endpoint = f"/messages/{message_id}/star"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class MessagePinView(APIView):
    """Pin/Unpin message"""
    permission_classes = [AllowAny]
    
    def post(self, request, message_id):
        """Pin message"""
        endpoint = f"/messages/{message_id}/pin"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, message_id):
        """Unpin message"""
        endpoint = f"/messages/{message_id}/pin"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))


class ChatsView(APIView):
    """Get chats"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/chats")
        return Response(result, status=result.get('status_code', 500))

class ChatView(APIView):
    """Chat management"""
    permission_classes = [AllowAny]
    
    def get(self, request, chat_id):
        """Get chat"""
        endpoint = f"/chats/{chat_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, chat_id):
        """Delete chat"""
        endpoint = f"/chats/{chat_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, chat_id):
        """Archive/Unarchive chat"""
        endpoint = f"/chats/{chat_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request, chat_id):
        """Chat Settings Management: Pin, Mute, Read, Disappearing"""
        endpoint = f"/chats/{chat_id}"
        result = make_whapi_request("PATCH", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class ContactsView(APIView):
    """Contacts management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get contacts"""
        result = make_whapi_request("GET", "/contacts")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Check phones"""
        result = make_whapi_request("POST", "/contacts", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class ContactView(APIView):
    """Contact management"""
    permission_classes = [AllowAny]
    
    def get(self, request, contact_id):
        """Get contact"""
        endpoint = f"/contacts/{contact_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, contact_id):
        """Send contact"""
        endpoint = f"/contacts/{contact_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def head(self, request, contact_id):
        """Check exist"""
        endpoint = f"/contacts/{contact_id}"
        result = make_whapi_request("HEAD", endpoint)
        return Response(result, status=result.get('status_code', 500))

class ContactProfileView(APIView):
    """Get contact profile"""
    permission_classes = [AllowAny]
    
    def get(self, request, contact_id):
        endpoint = f"/contacts/{contact_id}/profile"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class ContactLidsView(APIView):
    """Get LIDs"""
    permission_classes = [AllowAny]
    
    def get(self, request, contact_id=None):
        if contact_id:
            endpoint = f"/contacts/lids/{contact_id}"
        else:
            endpoint = "/contacts/lids"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))



class PresencesMeView(APIView):
    """Send online or offline presence"""
    permission_classes = [AllowAny]
    
    def put(self, request):
        result = make_whapi_request("PUT", "/presences/me", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class PresenceView(APIView):
    """Presence management"""
    permission_classes = [AllowAny]
    
    def get(self, request, entry_id):
        """Get presence"""
        endpoint = f"/presences/{entry_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, entry_id):
        """Subscribe to presence"""
        endpoint = f"/presences/{entry_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request, entry_id):
        """Send typing or recording presence"""
        endpoint = f"/presences/{entry_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class GroupsView(APIView):
    """Groups management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get groups"""
        result = make_whapi_request("GET", "/groups")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create group"""
        result = make_whapi_request("POST", "/groups", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request):
        """Accept group invite"""
        result = make_whapi_request("PUT", "/groups", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class GroupView(APIView):
    """Group management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group"""
        endpoint = f"/groups/{group_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request, group_id):
        """Update group info"""
        endpoint = f"/groups/{group_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, group_id):
        """Leave group"""
        endpoint = f"/groups/{group_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request, group_id):
        """Update group setting"""
        endpoint = f"/groups/{group_id}"
        result = make_whapi_request("PATCH", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class GroupInviteView(APIView):
    """Group invite management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group invite"""
        endpoint = f"/groups/{group_id}/invite"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, group_id):
        """Revoke group invite"""
        endpoint = f"/groups/{group_id}/invite"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class GroupParticipantsView(APIView):
    """Group participants management"""
    permission_classes = [AllowAny]
    
    def post(self, request, group_id):
        """Add group participant"""
        endpoint = f"/groups/{group_id}/participants"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, group_id):
        """Remove group participant"""
        endpoint = f"/groups/{group_id}/participants"
        result = make_whapi_request("DELETE", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class GroupIconView(APIView):
    """Group icon management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group icon"""
        endpoint = f"/groups/{group_id}/icon"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request, group_id):
        """Set group icon"""
        endpoint = f"/groups/{group_id}/icon"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, group_id):
        """Delete group icon"""
        endpoint = f"/groups/{group_id}/icon"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class GroupAdminsView(APIView):
    """Group admins management"""
    permission_classes = [AllowAny]
    
    def delete(self, request, group_id):
        """Demote group admin"""
        endpoint = f"/groups/{group_id}/admins"
        result = make_whapi_request("DELETE", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request, group_id):
        """Promote to group admin"""
        endpoint = f"/groups/{group_id}/admins"
        result = make_whapi_request("PATCH", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class GroupInviteLinkView(APIView):
    """Group invite link management"""
    permission_classes = [AllowAny]
    
    def post(self, request, invite_code):
        """Send group invite link"""
        endpoint = f"/groups/link/{invite_code}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def get(self, request, invite_code):
        """Get group info by invite code"""
        endpoint = f"/groups/link/{invite_code}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class GroupApplicationsView(APIView):
    """Group applications management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get list of join requests to the group"""
        endpoint = f"/groups/{group_id}/applications"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, group_id):
        """Accept group applications for listed users"""
        endpoint = f"/groups/{group_id}/applications"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, group_id):
        """Reject group applications for listed users"""
        endpoint = f"/groups/{group_id}/applications"
        result = make_whapi_request("DELETE", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))


class StoriesView(APIView):
    """Stories management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of stories"""
        result = make_whapi_request("GET", "/stories")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create & publish story"""
        result = make_whapi_request("POST", "/stories", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class StoriesSendTextView(APIView):
    """Post text story"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/stories/send/text", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class StoriesSendMediaView(APIView):
    """Post media story"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/stories/send/media", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class StoriesSendAudioView(APIView):
    """Post audio story"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/stories/send/audio", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class StoryView(APIView):
    """Story management"""
    permission_classes = [AllowAny]
    
    def get(self, request, message_id):
        """Get story"""
        endpoint = f"/stories/{message_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def put(self, request, message_id):
        """Copy story"""
        endpoint = f"/stories/{message_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))


class StatusesView(APIView):
    """Get message or story view statuses"""
    permission_classes = [AllowAny]
    
    def get(self, request, message_id):
        endpoint = f"/statuses/{message_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewslettersView(APIView):
    """Newsletters management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get newsletters"""
        result = make_whapi_request("GET", "/newsletters")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create newsletter"""
        result = make_whapi_request("POST", "/newsletters", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class NewslettersFindView(APIView):
    """Find newsletters by filters"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/newsletters/find")
        return Response(result, status=result.get('status_code', 500))

class NewslettersRecommendedView(APIView):
    """Get recommended newsletters by country"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/newsletters/recommended")
        return Response(result, status=result.get('status_code', 500))

class NewsletterView(APIView):
    """Newsletter management"""
    permission_classes = [AllowAny]
    
    def get(self, request, newsletter_id):
        """Get newsletter information"""
        endpoint = f"/newsletters/{newsletter_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, newsletter_id):
        """Delete newsletter"""
        endpoint = f"/newsletters/{newsletter_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request, newsletter_id):
        """Edit newsletter"""
        endpoint = f"/newsletters/{newsletter_id}"
        result = make_whapi_request("PATCH", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class NewsletterSubscriptionView(APIView):
    """Newsletter subscription management"""
    permission_classes = [AllowAny]
    
    def post(self, request, newsletter_id):
        """Subscribe to newsletter"""
        endpoint = f"/newsletters/{newsletter_id}/subscription"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, newsletter_id):
        """Unsubscribe from newsletter"""
        endpoint = f"/newsletters/{newsletter_id}/subscription"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewsletterInviteSubscriptionView(APIView):
    """Newsletter invite subscription management"""
    permission_classes = [AllowAny]
    
    def post(self, request, invite_code):
        """Subscribe to newsletter by invite code"""
        endpoint = f"/newsletters/invite/{invite_code}/subscription"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, invite_code):
        """Unsubscribe from newsletter by invite code"""
        endpoint = f"/newsletters/invite/{invite_code}/subscription"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewsletterTrackingView(APIView):
    """Subscribe to newsletter updates"""
    permission_classes = [AllowAny]
    
    def post(self, request, newsletter_id):
        endpoint = f"/newsletters/{newsletter_id}/tracking"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class NewsletterMessagesView(APIView):
    """Get newsletter messages"""
    permission_classes = [AllowAny]
    
    def get(self, request, newsletter_id):
        endpoint = f"/newsletters/{newsletter_id}/messages"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewsletterInviteView(APIView):
    """Newsletter admin invite management"""
    permission_classes = [AllowAny]
    
    def post(self, request, newsletter_id, contact_id):
        """Create Newsletter admin-invite"""
        endpoint = f"/newsletters/{newsletter_id}/invite/{contact_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, newsletter_id, contact_id):
        """Revoke Newsletter admin-invite"""
        endpoint = f"/newsletters/{newsletter_id}/invite/{contact_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewsletterAdminsView(APIView):
    """Newsletter admins management"""
    permission_classes = [AllowAny]
    
    def put(self, request, newsletter_id, contact_id):
        """Accept Newsletter admin-request"""
        endpoint = f"/newsletters/{newsletter_id}/admins/{contact_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, newsletter_id, contact_id):
        """Demote Newsletter admin"""
        endpoint = f"/newsletters/{newsletter_id}/admins/{contact_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class NewsletterLinkView(APIView):
    """Newsletter link management"""
    permission_classes = [AllowAny]
    
    def post(self, request, invite_code):
        """Send newsletter invite link"""
        endpoint = f"/newsletters/link/{invite_code}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def get(self, request, invite_code):
        """Get newsletter info by invite code"""
        endpoint = f"/newsletters/link/{invite_code}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))


class MediaView(APIView):
    """Media management"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Upload media"""
        result = make_whapi_request("POST", "/media", data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def get(self, request, media_id=None):
        if media_id:
            """Get media"""
            endpoint = f"/media/{media_id}"
        else:
            """Get media files"""
            endpoint = "/media"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, media_id):
        """Delete media"""
        endpoint = f"/media/{media_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))


class BusinessView(APIView):
    """Business profile management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get business profile"""
        result = make_whapi_request("GET", "/business")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Edit your Business Profile"""
        result = make_whapi_request("POST", "/business", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class BusinessProductsView(APIView):
    """Business products management"""
    permission_classes = [AllowAny]
    
    def get(self, request, contact_id=None):
        if contact_id:
            """Get products by Contact ID"""
            endpoint = f"/business/{contact_id}/products"
        else:
            """Get products"""
            endpoint = "/business/products"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create product"""
        result = make_whapi_request("POST", "/business/products", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class BusinessProductView(APIView):
    """Business product management"""
    permission_classes = [AllowAny]
    
    def get(self, request, product_id):
        """Get product"""
        endpoint = f"/business/products/{product_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, product_id):
        """Send product"""
        endpoint = f"/business/products/{product_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def patch(self, request, product_id):
        """Update product"""
        endpoint = f"/business/products/{product_id}"
        result = make_whapi_request("PATCH", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, product_id):
        """Delete product"""
        endpoint = f"/business/products/{product_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class BusinessOrdersView(APIView):
    """Business orders management"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Create order"""
        result = make_whapi_request("POST", "/business/orders", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class BusinessOrderView(APIView):
    """Get order items"""
    permission_classes = [AllowAny]
    
    def get(self, request, order_id):
        endpoint = f"/business/orders/{order_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class BusinessCartView(APIView):
    """Business cart management"""
    permission_classes = [AllowAny]
    
    def put(self, request):
        """Refresh cart"""
        result = make_whapi_request("PUT", "/business/cart", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class BusinessCartEnabledView(APIView):
    """Enable or disable cart"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/business/cart/enabled", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class BusinessCatalogView(APIView):
    """Send catalog by Contact ID"""
    permission_classes = [AllowAny]
    
    def post(self, request, contact_id):
        endpoint = f"/business/catalogs/{contact_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))


class LabelsView(APIView):
    """Labels management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get labels"""
        result = make_whapi_request("GET", "/labels")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create label"""
        result = make_whapi_request("POST", "/labels", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class LabelView(APIView):
    """Label management"""
    permission_classes = [AllowAny]
    
    def get(self, request, label_id):
        """Get objects associated with label"""
        endpoint = f"/labels/{label_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))

class LabelAssociationView(APIView):
    """Label association management"""
    permission_classes = [AllowAny]
    
    def post(self, request, label_id, association_id):
        """Add label association"""
        endpoint = f"/labels/{label_id}/{association_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, label_id, association_id):
        """Delete label association"""
        endpoint = f"/labels/{label_id}/{association_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))


class BlacklistView(APIView):
    """Blacklist management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get blacklist"""
        result = make_whapi_request("GET", "/blacklist")
        return Response(result, status=result.get('status_code', 500))

class BlacklistContactView(APIView):
    """Blacklist contact management"""
    permission_classes = [AllowAny]
    
    def put(self, request, contact_id):
        """Add contact to blacklist"""
        endpoint = f"/blacklist/{contact_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, contact_id):
        """Remove contact from blacklist"""
        endpoint = f"/blacklist/{contact_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))


class CommunitiesView(APIView):
    """Communities management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get communities"""
        result = make_whapi_request("GET", "/communities")
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Create community"""
        result = make_whapi_request("POST", "/communities", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class CommunityView(APIView):
    """Community management"""
    permission_classes = [AllowAny]
    
    def get(self, request, community_id):
        """Get community"""
        endpoint = f"/communities/{community_id}"
        result = make_whapi_request("GET", endpoint)
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, community_id):
        """Create group in community"""
        endpoint = f"/communities/{community_id}"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, community_id):
        """Deactivate community"""
        endpoint = f"/communities/{community_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class CommunityLinkView(APIView):
    """Revoke community invite code"""
    permission_classes = [AllowAny]
    
    def delete(self, request, community_id):
        endpoint = f"/communities/{community_id}/link"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class CommunityGroupView(APIView):
    """Community group management"""
    permission_classes = [AllowAny]
    
    def put(self, request, community_id, group_id):
        """Link group to community"""
        endpoint = f"/communities/{community_id}/{group_id}"
        result = make_whapi_request("PUT", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, community_id, group_id):
        """Unlink group from community"""
        endpoint = f"/communities/{community_id}/{group_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class CommunityGroupJoinView(APIView):
    """Join in community group"""
    permission_classes = [AllowAny]
    
    def post(self, request, community_id, group_id):
        endpoint = f"/communities/{community_id}/{group_id}/join"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))


class BotsView(APIView):
    """Get bots"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        result = make_whapi_request("GET", "/bots")
        return Response(result, status=result.get('status_code', 500))


class CallsView(APIView):
    """Calls management"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Create call event"""
        result = make_whapi_request("POST", "/calls", data=request.data)
        return Response(result, status=result.get('status_code', 500))

class CallView(APIView):
    """Call management"""
    permission_classes = [AllowAny]
    
    def delete(self, request, call_id):
        """Reject call"""
        endpoint = f"/calls/{call_id}"
        result = make_whapi_request("DELETE", endpoint)
        return Response(result, status=result.get('status_code', 500))

class CallRejectView(APIView):
    """Reject call"""
    permission_classes = [AllowAny]
    
    def post(self, request, call_id):
        endpoint = f"/calls/{call_id}/reject"
        result = make_whapi_request("POST", endpoint, data=request.data)
        return Response(result, status=result.get('status_code', 500))

class CallsGroupLinkView(APIView):
    """Create group video call link"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        result = make_whapi_request("POST", "/calls/group_link", data=request.data)
        return Response(result, status=result.get('status_code', 500))

