from django.shortcuts import render

# Create your views here.
import json
import os
import requests
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from boostedchatScrapper.spiders.facebook_group_member_scrapper import scrap_facebook_group_members 
from boostedchatScrapper.spiders.facebook_send_first_message import send_first_message
from .forms import ScrapFacebookGroupForm, SendFirstMessageForm

from .models import ChatSession
from .prompts import system_prompt

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv("TOKEN")  # Set this to a secret string you choose

@schema_context(os.getenv("SCHEMA_NAME"))
def query_gpt(prompt,recipient_id=None):
    # declare chat_session variable
    chat_session= None
    if recipient_id is not None:
        try:
            # Check if session exists
            chat_session = ChatSession.objects.get(recipient_id=recipient_id)
            chat_session.add_message("user", prompt)
        except ChatSession.DoesNotExist:
            conversation_history=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
            chat_session = ChatSession.objects.create(
                recipient_id=recipient_id,
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

    return gpt_response

@api_view(['GET', 'POST'])
def webhook(request):
    """
    request from facebook post looks like:
    {'object': 'page', 'entry': [{'time': 1745483896270, 'id': '100747912772086', 'messaging': [{'sender': {'id': '9784957798194096'}, 'recipient': {'id': '100747912772086'}, 'timestamp': 1745483895815, 'message': {'mid': 'm_r6NHj8BWOWVSQkWzoHFoGyUkvyqnSW7o0hfluI2whxeYioAcNozLLN_eG9pCd93V5C-SeXC4-ikJX5hmg_bCWQ', 'text': 'give me more information about last expense?'}}]}]}
    """
    if request.method == 'GET':
        print(request.GET)
        # Verification
        # Check if the request is a verification request
        if (request.GET.get("hub.mode") == "subscribe" and
            request.GET.get("hub.verify_token") == VERIFY_TOKEN):
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

        # Handle incoming messages
        data = json.loads(request.body.decode('utf-8'))
        logging.warning(data)

        if data.get('object') == 'page':
            # raise Exception("Webhook received a page object")
            # continue
            # send_message("9581548405296563","Been hustling hard")
            
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message') and messaging_event['message'].get('is_echo'):
                        # Ignore messages sent by the page itself to prevent loops
                        continue
                    sender_id = messaging_event['sender']['id']

                    if 'message' in messaging_event:
                        message_text = messaging_event['message'].get('text')
                        if message_text:
                            # Get user profile for personalization
                            # user_profile = get_user_profile(sender_id)
                            # first_name = user_profile.get('first_name', '')

                            # Create personalized reply
                            # reply = f"Hi {first_name}! You said: {message_text}"

                            # Send reply
                            output_message = query_gpt(message_text,sender_id)
                            send_message(sender_id, output_message)
                            # break
                            # continue

            return Response({"success":True},status=status.HTTP_200_OK)
        # else:
            # return HttpResponse(status=404)

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

@api_view(['POST'])
def scrap_facebook_group_members_api(request):
    """Scrap facebook group members"""
    # import pdb;pdb.set_trace()
    data = request.data
    # data = json.loads(request.body.decode('utf-8'))
    
    group_url = data.get('group_url')
    cookies_ = data.get('cookies')
    # cookies_ = request.POST.get('cookies')
    # cookies_ = json.loads(cookies_)
    # cookies_ = json.loads(cookies_)
    # cookies_ = json.loads(cookies_)
    print(group_url)
    print(cookies_)
    member_data = scrap_facebook_group_members(cookies_,group_url=group_url)
    return JsonResponse(member_data, safe=False)

@api_view(['POST'])
def send_first_message_api(request):
    """Send first message to user"""
    data = json.loads(request.body.decode('utf-8'))
    username = data.get('username')
    cookies_ = data.get('cookies')
    message = data.get('message')
    cookies_ = request.POST.get('cookies')
    # cookies_ = json.loads(cookies_)
    # cookies_ = json.loads(cookies_)
    # cookies_ = json.loads(cookies_)
    print(username)
    print(cookies_)
    send_first_message(cookies_=cookies_,username=username,message=message)
    return JsonResponse({"status":"success"})


@csrf_exempt
def scrap_facebook_group_members_view(request):
    """Scrap facebook group members"""
    if request.method == 'POST':
        form = ScrapFacebookGroupForm(request.POST)
        if form.is_valid():
            group_url = form.cleaned_data['group_url']
            cookies_ = form.cleaned_data['cookies']
            # import pdb;pdb.set_trace()
            cookies_ = json.loads(cookies_)
            # cookies_ = json.loads(cookies_)
            # cookies_ = json.loads(cookies_)

            print(group_url)
            print(cookies_)
            member_data = scrap_facebook_group_members(cookies_,group_url=group_url)
            print(member_data)
            return JsonResponse(member_data, safe=False)
    else:
        form = ScrapFacebookGroupForm()
    return render(request, 'facebook/scrap_facebook_group_members.html', {'form': form})


@csrf_exempt
def send_first_message_view(request):
    """Send first message to user"""
    if request.method == 'POST':
        form = SendFirstMessageForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            cookies_ = form.cleaned_data['cookies']
            message = form.cleaned_data['message']
            cookies_ = json.loads(cookies_)
            # cookies_ = json.loads(cookies_)
            # cookies_ = json.loads(cookies_)
            print(username)
            print(cookies_)
            send_first_message(cookies_=cookies_,username=username,message=message)
            return JsonResponse({"status":"success"})
    else:
        form = SendFirstMessageForm()
    return render(request, 'facebook/send_first_message.html', {'form': form})

