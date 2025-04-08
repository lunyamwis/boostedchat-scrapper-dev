from django.shortcuts import render

# Create your views here.
import json
import requests
import uuid
import logging
import os
import re

from dotenv import load_dotenv
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import AllowAny

from .tasks import send_batch_whatsapp_text_with_template

# Define constants




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
            except json.JSONDecodeError as e:
                return Response({"error": "Invalid JSON data"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            numbers = data.get('numbers', [])
            names = data.get('names', [])
            progress = data.get('progress', False)
            paragraphs = data.get('paragraphs', [])

            if not numbers or not names or not paragraphs:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            if len(numbers) != len(names):
                return Response({"error": "Numbers and names lists must be of equal length"}, status=status.HTTP_400_BAD_REQUEST)

            send_batch_whatsapp_text_with_template.delay(numbers, names, progress, paragraphs)
            return Response({"message": "Task initiated successfully"}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
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
        print(request.data)
        request_data = request.data  # Access POST data via request.data

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
    user_prompt = extract_string_from_reply(message)
    if user_prompt == "yes":
        send_message(message, phonenumber, "TALK_TO_AN_AGENT", name)
    elif user_prompt == "no":
        print("Chat terminated")
    else:
        if re.search("njugu", user_prompt):
            send_message(message, phonenumber, "SERVICE_INTRO_TEXT", name)

        elif re.search(
            "help|contact|reach|email|problem|issue|more|information", user_prompt
        ):
            send_message(message, phonenumber, "CONTACT_US", name)

        elif re.search("hello|hi|greetings", user_prompt):
            
            if re.search("this", user_prompt):
                send_message(message, phonenumber, "CHATBOT", name)

            else:
                print(user_prompt)
                send_message(message, phonenumber, "SEND_GREETINGS_AND_PROMPT", name)

        else:
            send_message(message, phonenumber, "CHATBOT", name)

def query_gpt(prompt):
    body = {
        "model": "gpt-4-1106-preview",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

    res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
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
        # hotelonline_response = requests.post(f"https://{os.getenv('DOMAIN')}/whatsapp/generateResponse/",data={"question":message,"phone_number":str(phone_number)})
        # output_message = hotelonline_response.json()['message']
        output_message = query_gpt(message)["choices"][0]["message"]["content"]
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
