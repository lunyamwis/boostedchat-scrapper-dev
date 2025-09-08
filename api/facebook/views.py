from django.shortcuts import render
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from boostedchatScrapper.spiders.facebook_group_member_scrapper import scrap_facebook_group_members 
from boostedchatScrapper.spiders.facebook_send_first_message import send_first_message
from .forms import ScrapFacebookGroupForm, SendFirstMessageForm
from .models import ChatSession
from .prompts import system_prompt


PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv("TOKEN")
APP_ID = os.getenv('FACEBOOK_APP_ID')
APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')

# Base Graph API URL
GRAPH_API_BASE_URL = "https://graph.facebook.com/v18.0"

# Helper function for Facebook API requests
def make_facebook_request(method: str, endpoint: str, params: Dict = None, data: Dict = None, access_token: str = None) -> Dict:
    """Helper function to make requests to Facebook Graph API"""
    url = f"{GRAPH_API_BASE_URL}{endpoint}"
    
    if not access_token:
        access_token = PAGE_ACCESS_TOKEN
    
    if params is None:
        params = {}
    params['access_token'] = access_token
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, params=params, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, params=params)
        elif method.upper() == 'PUT':
            response = requests.put(url, params=params, json=data)
        else:
            return {"success": False, "error": "Unsupported HTTP method"}
        
        response.raise_for_status()
        return {"success": True, "data": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "status_code": getattr(e.response, 'status_code', 500)}

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
    """Your existing webhook function"""
    if request.method == 'GET':
        print(request.GET)
        if (request.GET.get("hub.mode") == "subscribe" and
            request.GET.get("hub.verify_token") == VERIFY_TOKEN):
            challenge = request.GET.get("hub.challenge")
            print(challenge)
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse("Verification failed", status=403)
    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        logging.warning(data)

        if data.get('object') == 'page':            
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message') and messaging_event['message'].get('is_echo'):
                        continue
                    sender_id = messaging_event['sender']['id']

                    if 'message' in messaging_event:
                        message_text = messaging_event['message'].get('text')
                        if message_text:
                            output_message = query_gpt(message_text,sender_id)
                            send_message(sender_id, output_message)

            return Response({"success":True},status=status.HTTP_200_OK)

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

# Your existing scraping functions (keep them as they are)
@api_view(['POST'])
def scrap_facebook_group_members_api(request):
    """Scrap facebook group members"""
    data = request.data
    group_url = data.get('group_url')
    cookies_ = data.get('cookies')
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
            cookies_ = json.loads(cookies_)
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
            print(username)
            print(cookies_)
            send_first_message(cookies_=cookies_,username=username,message=message)
            return JsonResponse({"status":"success"})
    else:
        form = SendFirstMessageForm()
    return render(request, 'facebook/send_first_message.html', {'form': form})


class FacebookAuthURLView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        facebook_auth_url = (
            f"https://www.facebook.com/v12.0/dialog/oauth?"
            f"client_id={os.getenv('FACEBOOK_APP_ID')}"
            f"&redirect_uri={os.getenv('FACEBOOK_REDIRECT_URI')}"
            f"&state=some_random_state"
            f"&scope=email"
        )
        return Response({"auth_url": facebook_auth_url})


class FacebookAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=400)

        # Exchange code for access token
        token_url = (
            f"https://graph.facebook.com/v12.0/oauth/access_token?"
            f"client_id={os.getenv('FACEBOOK_APP_ID')}"
            f"&redirect_uri={os.getenv('FACEBOOK_REDIRECT_URI')}"
            f"&client_secret={os.getenv('FACEBOOK_APP_SECRET')}"
            f"&code={code}"
        )
        token_response = requests.get(token_url)
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return Response({"error": "Failed to get access token", "details": token_data}, status=400)

        # Get user profile info
        profile_url = (
            f"https://graph.facebook.com/me?"
            f"fields=id,name"
            f"&access_token={access_token}"
        )
        profile_response = requests.get(profile_url)
        profile_data = profile_response.json()

        # Here you would typically create or get the user and issue your own JWT token or session
        return Response({
            "facebook_profile": profile_data,
            "facebook_access_token": access_token
        })

class FacebookUserView(APIView):
    """Facebook User management"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user profile"""
        fields = request.query_params.get('fields', 'id,name')
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET", 
            f"/{user_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookUserAccountsView(APIView):
    """Get user's pages/accounts"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user's accounts/pages"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{user_id}/accounts",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookUserPermissionsView(APIView):
    """Get user permissions"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id="me"):
        """Get user permissions"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{user_id}/permissions",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPageView(APIView):
    """Facebook Page management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page information"""
        fields = request.query_params.get('fields', 'id,name,about,category,fan_count,followers_count,website,phone,location')
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Update page information"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPageInsightsView(APIView):
    """Page insights/analytics"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page insights"""
        metric = request.query_params.get('metric', 'page_fans')
        period = request.query_params.get('period', 'day')
        since = request.query_params.get('since')
        until = request.query_params.get('until')
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        params = {'metric': metric, 'period': period}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/insights",
            params=params,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPageConversationsView(APIView):
    """Page conversations"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page conversations"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/conversations",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPostsView(APIView):
    """Facebook Posts management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page posts"""
        fields = request.query_params.get('fields', 'id,message,created_time,likes.summary(true),comments.summary(true),shares')
        limit = request.query_params.get('limit', 25)
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/posts",
            params={'fields': fields, 'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create a post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/feed",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostView(APIView):
    """Single post management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get specific post"""
        fields = request.query_params.get('fields', 'id,message,created_time,likes.summary(true),comments.summary(true),shares')
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Update post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, post_id):
        """Delete post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "DELETE",
            f"/{post_id}",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostLikesView(APIView):
    """Post likes management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get post likes"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}/likes",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Like a post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}/likes",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, post_id):
        """Unlike a post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "DELETE",
            f"/{post_id}/likes",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookPostCommentsView(APIView):
    """Post comments management"""
    permission_classes = [AllowAny]
    
    def get(self, request, post_id):
        """Get post comments"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        order = request.query_params.get('order', 'chronological')
        
        result = make_facebook_request(
            "GET",
            f"/{post_id}/comments",
            params={'limit': limit, 'order': order},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, post_id):
        """Comment on post"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{post_id}/comments",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookCommentView(APIView):
    """Comment management"""
    permission_classes = [AllowAny]
    
    def get(self, request, comment_id):
        """Get comment"""
        fields = request.query_params.get('fields', 'id,message,created_time,from,likes.summary(true)')
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{comment_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, comment_id):
        """Update comment"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{comment_id}",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request, comment_id):
        """Delete comment"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "DELETE",
            f"/{comment_id}",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookMessagesView(APIView):
    """Messenger Platform - Send Messages"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Send message via Messenger Platform"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        # Enhanced message sending with various message types
        payload = {
            'messaging_type': request.data.get('messaging_type', 'RESPONSE'),
            'recipient': request.data.get('recipient'),
            'message': request.data.get('message')
        }
        
        # Add optional fields
        if 'sender_action' in request.data:
            payload['sender_action'] = request.data['sender_action']
        if 'notification_type' in request.data:
            payload['notification_type'] = request.data['notification_type']
        if 'tag' in request.data:
            payload['tag'] = request.data['tag']
        
        result = make_facebook_request(
            "POST",
            "/me/messages",
            data=payload,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookMessengerProfileView(APIView):
    """Messenger Profile API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get Messenger Profile"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        fields = request.query_params.get('fields', 'get_started,greeting,persistent_menu')
        
        result = make_facebook_request(
            "GET",
            "/me/messenger_profile",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request):
        """Set Messenger Profile"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            "/me/messenger_profile",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def delete(self, request):
        """Delete Messenger Profile fields"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "DELETE",
            "/me/messenger_profile",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookPhotosView(APIView):
    """Photos management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page photos"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/photos",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Upload photo"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/photos",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookVideosView(APIView):
    """Videos management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page videos"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/videos",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Upload video"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/videos",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookAlbumsView(APIView):
    """Albums management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page albums"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/albums",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create album"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/albums",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookEventsView(APIView):
    """Events management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get page events"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        fields = request.query_params.get('fields', 'id,name,description,start_time,end_time,place')
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/events",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Create event"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/events",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookEventView(APIView):
    """Single event management"""
    permission_classes = [AllowAny]
    
    def get(self, request, event_id):
        """Get event details"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        fields = request.query_params.get('fields', 'id,name,description,start_time,end_time,place,attending_count')
        
        result = make_facebook_request(
            "GET",
            f"/{event_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookGroupView(APIView):
    """Single group management"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group details"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        fields = request.query_params.get('fields', 'id,name,description,privacy,member_count')
        
        result = make_facebook_request(
            "GET",
            f"/{group_id}",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookGroupFeedView(APIView):
    """Group feed"""
    permission_classes = [AllowAny]
    
    def get(self, request, group_id):
        """Get group feed"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        limit = request.query_params.get('limit', 25)
        
        result = make_facebook_request(
            "GET",
            f"/{group_id}/feed",
            params={'limit': limit},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, group_id):
        """Post to group"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{group_id}/feed",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookWebhookSubscriptionsView(APIView):
    """Webhook subscriptions management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get webhook subscriptions"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/subscriptions",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, page_id):
        """Subscribe to webhooks"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{page_id}/subscriptions",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookLeadGenFormsView(APIView):
    """Lead generation forms"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get lead forms"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}/leadgen_forms",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookLeadsView(APIView):
    """Leads management"""
    permission_classes = [AllowAny]
    
    def get(self, request, form_id):
        """Get leads from form"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{form_id}/leads",
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookInstagramAccountView(APIView):
    """Instagram account management"""
    permission_classes = [AllowAny]
    
    def get(self, request, page_id):
        """Get connected Instagram account"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "GET",
            f"/{page_id}",
            params={'fields': 'instagram_business_account'},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookInstagramMediaView(APIView):
    """Instagram media management"""
    permission_classes = [AllowAny]
    
    def get(self, request, instagram_account_id):
        """Get Instagram media"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        fields = request.query_params.get('fields', 'id,caption,media_type,media_url,timestamp')
        
        result = make_facebook_request(
            "GET",
            f"/{instagram_account_id}/media",
            params={'fields': fields},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))
    
    def post(self, request, instagram_account_id):
        """Create Instagram media"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        result = make_facebook_request(
            "POST",
            f"/{instagram_account_id}/media",
            data=request.data,
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))

class FacebookDebugTokenView(APIView):
    """Debug access token"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Debug access token"""
        input_token = request.query_params.get('input_token', PAGE_ACCESS_TOKEN)
        access_token = f"{APP_ID}|{APP_SECRET}"
        
        result = make_facebook_request(
            "GET",
            "/debug_token",
            params={'input_token': input_token},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))


class FacebookBatchRequestView(APIView):
    """Batch requests"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Execute batch requests"""
        access_token = request.query_params.get('access_token', PAGE_ACCESS_TOKEN)
        
        batch_requests = request.data.get('batch', [])
        
        result = make_facebook_request(
            "POST",
            "/",
            data={'batch': json.dumps(batch_requests)},
            access_token=access_token
        )
        
        return Response(result, status=result.get('status_code', 500))