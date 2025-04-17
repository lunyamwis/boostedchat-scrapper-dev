from django.shortcuts import render

# Create your views here.
import json
import os
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv("TOKEN")  # Set this to a secret string you choose

@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        # Facebook webhook verification
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Verification token mismatch', status=403)

    elif request.method == 'POST':
        # Handle incoming messages
        data = json.loads(request.body.decode('utf-8'))

        if data.get('object') == 'page':
            send_message("9581548405296563","Been hustling hard")
            # for entry in data.get('entry', []):
            #     for messaging_event in entry.get('messaging', []):
            #         sender_id = messaging_event['sender']['id']

            #         if 'message' in messaging_event:
            #             message_text = messaging_event['message'].get('text')
            #             if message_text:
            #                 # Get user profile for personalization
            #                 # user_profile = get_user_profile(sender_id)
            #                 # first_name = user_profile.get('first_name', '')

            #                 # Create personalized reply
            #                 # reply = f"Hi {first_name}! You said: {message_text}"

            #                 # Send reply
            #                 # send_message(sender_id, reply)

            return HttpResponse('EVENT_RECEIVED')
        else:
            return HttpResponse(status=404)

def get_user_profile(user_id):
    """Fetch user profile info from Facebook Graph API"""
    url = f"https://graph.facebook.com/v22.0/{user_id}"
    params = {
        'fields': 'first_name,last_name,profile_pic',
        'access_token': PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def send_message(recipient_id, message_text):
    """Send message to user via Facebook Send API"""
    url = f"https://graph.facebook.com/v22.0/me/messages"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'messaging_type': 'RESPONSE',
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    params = {'access_token': PAGE_ACCESS_TOKEN}
    response = requests.post(url, headers=headers, params=params, json=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
